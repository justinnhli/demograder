import sys
from collections import defaultdict
from itertools import product
from os import environ, chmod, walk
from os.path import basename, dirname, join as join_path, realpath
from shutil import copyfile
from subprocess import run as run_process, PIPE
from tempfile import TemporaryDirectory

import django

sys.path.append(join_path(dirname(realpath(__file__)), '..'))
environ.setdefault('DJANGO_SETTINGS_MODULE', 'demograder.settings')
django.setup()

import django_rq
from rq.timeouts import JobTimeoutException

DGLIB = join_path(dirname(realpath(__file__)), 'dglib.py')


def recursive_chmod(path):
    chmod(path, 0o777)
    for root, dirs, files in walk(path):
        for d in dirs:
            chmod(join_path(root, d), 0o777)
        for f in files:
            chmod(join_path(root, f), 0o777)


def evaluate_submission(result_id):
    from demograder.models import Result, ResultDependency
    result = Result.objects.get(pk=result_id)
    # create temporary directory
    with TemporaryDirectory() as temp_dir:
        # copy dglib library
        tmp_dglib = copyfile(DGLIB, join_path(temp_dir, basename(DGLIB)))
        # copy the submission script
        tmp_script = copyfile(result.project.script.name, join_path(temp_dir, basename(result.project.script.name)))
        # copy the submission
        tmp_uploads = []
        for upload in result.submission.uploads():
            tmp_uploads.append(copyfile(upload.file.name, join_path(temp_dir, basename(upload.file.name))))
        # copy all dependency files
        tmp_args = defaultdict(list)
        for result_dependency in ResultDependency.objects.filter(result=result):
            keyword = result_dependency.project_dependency.keyword
            for upstream_submission in result_dependency.producer.uploads():
                filepath = upstream_submission.file.name
                tmp_args[keyword].append(copyfile(filepath, join_path(temp_dir, basename(filepath))))
        timeout = result.project.timeout
        recursive_chmod(temp_dir)
        try:
            args = ['--_script', tmp_script, '--_uploads', ','.join(tmp_uploads)]
            for key, files in tmp_args.items():
                args.extend(('--{}'.format(key), ','.join(files)))
            args = ['sudo', '-u', 'nobody', sys.executable, '-B', tmp_dglib] + args
            completed_process = run_process(args, timeout=timeout, stderr=PIPE, stdout=PIPE)
            stdout = completed_process.stdout.decode('utf-8')
            stderr = completed_process.stderr.decode('utf-8')
            return_code = completed_process.returncode
        except JobTimeoutException:
            stdout = ''
            stderr = 'The program failed to complete within {} seconds and was terminated.'.format(result.project.timeout)
            return_code = 1
    # update Result
    result.stdout = stdout.strip()
    result.stderr = stderr.strip()
    result.return_code = return_code
    result.save()


def enqueue_submission_evaluation(result_id, timeout=10):
    django_rq.get_queue('evaluation').enqueue(evaluate_submission, result_id, timeout=timeout)


def get_relevant_submissions(person, project):
    from demograder.models import Project, Submission
    try:
        if project.submission_type == Project.LATEST:
            return (person.submissions().filter(project=project).latest(), )
        elif project.submission_type == Project.ALL:
            return tuple(person.submissions().filter(project=project))
        elif project.submission_type == Project.MULTIPLE:
            return tuple() # FIXME not implemented
    except Submission.DoesNotExist:
        return tuple()


def dispatch_submission(submission_id):
    from demograder.models import ProjectDependency, Submission, Result, ResultDependency
    submission = Submission.objects.get(pk=submission_id)
    project = submission.project
    if not project.script:
        return
    student = submission.student
    project_dependencies = sorted(project.upstream_dependencies(), key=(lambda pd: pd.keyword))
    dependents = defaultdict(set)
    for project_dependency in project_dependencies:
        if project_dependency.dependency_structure == ProjectDependency.SELF:
            dependents[project_dependency].update(get_relevant_submissions(student, project_dependency.producer))
        elif project_dependency.dependency_structure == ProjectDependency.INSTRUCTOR:
            dependents[project_dependency].update(
                get_relevant_submissions(project.course.instructor, project_dependency.producer)
            )
        elif project_dependency.dependency_structure == ProjectDependency.CLIQUE:
            dependents[project_dependency].update(
                get_relevant_submissions(project.course.instructor, project_dependency.producer)
            )
            for classmate in project.course.enrolled_students():
                dependents[project_dependency].update(get_relevant_submissions(classmate, project_dependency.producer))
        elif project_dependency.dependency_structure == ProjectDependency.CUSTOM:
            pass # FIXME not implemented
    for dependent_submissions in product(*(dependents[pd] for pd in project_dependencies)):
        result = Result(
            submission=submission,
        )
        result.save()
        kwargs = dict(zip(project_dependencies, dependent_submissions))
        for project_dependency, upstream_submission in kwargs.items():
            ResultDependency(
                result=result,
                project_dependency=project_dependency,
                producer=upstream_submission,
            ).save()
        enqueue_submission_evaluation(result.id, timeout=project.timeout + 1)


def enqueue_submission_dispatch(submission_id):
    django_rq.get_queue('dispatch').enqueue(dispatch_submission, submission_id)
