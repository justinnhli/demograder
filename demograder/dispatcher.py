import sys
from collections import defaultdict
from itertools import product
from os import chdir, chmod, environ, getcwd, walk
from os.path import basename, dirname, join as join_path, realpath
from shutil import copyfile
from sqlite3 import OperationalError as SQLiteOperationalError
from subprocess import run as run_process, PIPE
from tempfile import TemporaryDirectory

import django
from django.db.utils import OperationalError as DjangoOperationalError

sys.path.append(join_path(dirname(realpath(__file__)), '..'))
environ.setdefault('DJANGO_SETTINGS_MODULE', 'demograder.settings')
django.setup()

import django_rq

from demograder.models import Assignment, Project, ProjectDependency, Submission, Result, ResultDependency

DGLIB = join_path(dirname(realpath(__file__)), 'dglib.py')


def recursive_chmod(path):
    chmod(path, 0o777)
    for root, dirs, files in walk(path):
        for d in dirs:
            chmod(join_path(root, d), 0o777)
        for f in files:
            chmod(join_path(root, f), 0o777)


def prepare_files(result, temp_dir, timeout):
    # copy dglib library
    copyfile(DGLIB, join_path(temp_dir, basename(DGLIB)))
    # copy the submission script manually, to avoid line ending issues
    tmp_script = join_path(temp_dir, basename(result.project.script.name))
    with open(result.project.script.name) as in_fd:
        with open(tmp_script, 'w') as out_fd:
            for line in in_fd:
                out_fd.write(line)
    # copy the submission
    tmp_uploads = []
    for upload in result.submission.uploads():
        tmp_uploads.append(copyfile(upload.file.name, join_path(temp_dir, upload.project_file.filename)))
    # copy all dependency files
    tmp_args = defaultdict(list)
    for result_dependency in ResultDependency.objects.filter(result=result):
        keyword = result_dependency.project_dependency.keyword
        for upstream_upload in result_dependency.producer.uploads():
            filepath = upstream_upload.file.name
            tmp_args[keyword].append(copyfile(filepath, join_path(temp_dir, upstream_upload.project_file.filename)))
    recursive_chmod(temp_dir)
    return ['sudo', '-u', 'nobody', 'timeout', '-s', 'KILL', str(timeout), tmp_script]


def evaluate_submission(result_id):
    try:
        result = Result.objects.get(pk=result_id)
        timeout = result.project.timeout
        # create temporary directory
        with TemporaryDirectory() as temp_dir:
            cmd = prepare_files(result, temp_dir, timeout)
            old_cwd = getcwd()
            chdir(temp_dir)
            completed_process = run_process(cmd, stderr=PIPE, stdout=PIPE, check=False)
            stdout = completed_process.stdout.decode('utf-8')[:2**16]
            stderr = completed_process.stderr.decode('utf-8')[:2**16]
            return_code = completed_process.returncode
            if return_code == -9: # from timeout
                stderr += '\n\n'
                stderr += 'The program failed to complete within {} seconds and was terminated.'.format(timeout)
                stderr = stderr.strip()
            chdir(old_cwd)
        # update Result
        result.stdout = stdout.strip()
        result.stderr = stderr.strip()
        result.return_code = return_code
        result.save()
    except (SQLiteOperationalError, DjangoOperationalError):
        enqueue_submission_evaluation(result_id)
        return


def enqueue_submission_evaluation(result_id):
    django_rq.get_queue('evaluation').enqueue(evaluate_submission, result_id)


def get_relevant_submissions(person, project):
    try:
        if project.submission_type == Project.LATEST:
            return (person.submissions().filter(project=project).latest(), )
        elif project.submission_type == Project.ALL:
            return tuple(person.submissions().filter(project=project))
        # FIXME deal with other submission types
        return tuple()
    except Submission.DoesNotExist:
        return tuple()


def dispatch_submission(submission_id):
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
    for dependency, submissions in dependents.items():
        dependents[dependency] = sorted(submissions, key=(lambda submission: submission.timestamp))
    count = 0
    for dependent_submissions in product(*(dependents[pd] for pd in project_dependencies)):
        result = Result(submission=submission)
        result.save()
        kwargs = dict(zip(project_dependencies, dependent_submissions))
        for project_dependency, upstream_submission in kwargs.items():
            ResultDependency(
                result=result,
                project_dependency=project_dependency,
                producer=upstream_submission,
            ).save()
        enqueue_submission_evaluation(result.id)
        count += 1
        # TODO 200 was arbitrarily chosen; in the future this should be a project property
        if count == 200:
            break


def enqueue_submission_dispatch(submission_id):
    submission = Submission.objects.get(pk=submission_id)
    submission.result_set.all().delete()
    django_rq.get_queue('dispatch').enqueue(dispatch_submission, submission_id)


def dispatch_project(project_id):
    project = Project.objects.get(pk=project_id)
    for student in project.course.enrolled_students():
        submission = student.latest_submission(project=project)
        if submission:
            enqueue_submission_dispatch(submission.id)


def enqueue_project_dispatch(project_id):
    django_rq.get_queue('dispatch').enqueue(dispatch_project, project_id)


def dispatch_assignment(assignment_id):
    for project in Assignment.objects.get(pk=assignment_id).projects():
        enqueue_project_dispatch(project.id)


def enqueue_assignment_dispatch(assignment_id):
    django_rq.get_queue('dispatch').enqueue(dispatch_assignment, assignment_id)


def dispatch_tbd():
    for result in Result.objects.filter(return_code=None):
        enqueue_submission_evaluation(result.id)


def enqueue_tbd_dispatch():
    django_rq.get_queue('dispatch').enqueue(dispatch_tbd)


def clear_evaluation_queue():
    django_rq.get_queue('evaluation').empty()
