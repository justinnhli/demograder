import sys
from collections import defaultdict
from itertools import product
from os import chdir, chmod, environ, getcwd, walk
from os.path import basename, dirname, join as join_path, realpath
from shutil import copyfile, chown
from sqlite3 import OperationalError as SQLiteOperationalError
from subprocess import run as run_process, PIPE, TimeoutExpired
from tempfile import TemporaryDirectory

import django
from django.db.utils import OperationalError as DjangoOperationalError
from rq.timeouts import JobTimeoutException

sys.path.append(join_path(dirname(realpath(__file__)), '..'))
environ.setdefault('DJANGO_SETTINGS_MODULE', 'demograder.settings')

DGLIB = join_path(dirname(realpath(__file__)), 'dglib.py')


django.setup()

import django_rq
from demograder.models import Project, ProjectDependency, Submission, Result, ResultDependency


def recursive_chmod(path):
    chmod(path, 0o777)
    for root, dirs, files in walk(path):
        for d in dirs:
            chmod(join_path(root, d), 0o777)
        for f in files:
            chmod(join_path(root, f), 0o777)

def recursive_chown(path):
    chown(path, user='justinnhli', group='justinnhli')
    for root, dirs, files in walk(path):
        for d in dirs:
            chown(join_path(root, d), user='justinnhli', group='justinnhli')
        for f in files:
            chown(join_path(root, f), user='justinnhli', group='justinnhli')


def prepare_files(result, temp_dir):
    # copy dglib library
    # FIXME solution is to put dglib on pythonpath, not to copy it
    copyfile(DGLIB, join_path(temp_dir, basename(DGLIB)))
    # breadth first search and copy submission and all dependencies
    result_queue = [result]
    visited = set()
    while result_queue:
        dependency = result_queue.pop(0)
        visited.add(dependency.id)
        # copy files from this dependency
        for upload in dependency.submission.uploads():
            filename = upload.project_file.filename
            # not sure what to do if filenames conflict
            copyfile(upload.file.name, join_path(temp_dir, filename))
        # add dependencies to the queue
        for result_dependency in ResultDependency.objects.filter(result=dependency):
            if result_dependency.producer not in visited:
                result_queue.append(result_dependency.producer)
    recursive_chmod(temp_dir)
    return cmd


def evaluate_submission(result_id):
    try:
        result = Result.objects.get(pk=result_id)
        # create temporary directory
        with TemporaryDirectory() as temp_dir:
            cmd = prepare_files(result, temp_dir)
            old_cwd = getcwd()
            chdir(temp_dir)
            try:
                completed_process = run_process(cmd, timeout=result.project.timeout, stderr=PIPE, stdout=PIPE)
                stdout = completed_process.stdout.decode('utf-8')
                stderr = completed_process.stderr.decode('utf-8')
                return_code = completed_process.returncode
            except TimeoutExpired as e:
                stdout = e.stdout.decode('utf-8')
                stdout += '\n\n'
                stdout += 'The program failed to complete within {} seconds and was terminated.'.format(result.project.timeout)
                stderr = e.stderr.decode('utf-8')
                return_code = 1
            except JobTimeoutException:
                stdout = ''
                stderr = 'The program failed to complete within {} seconds and was terminated.'.format(result.project.timeout)
                return_code = 1
            chdir(old_cwd)
            recursive_chown(temp_dir)
            recursive_chmod(temp_dir)
        # update Result
        result.stdout = stdout.strip()
        result.stderr = stderr.strip()
        result.return_code = return_code
        result.save()
    except (JobTimeoutException, SQLiteOperationalError, DjangoOperationalError):
        enqueue_submission_evaluation(result_id)
        return


def enqueue_submission_evaluation(result_id, timeout=10):
    django_rq.get_queue('evaluation').enqueue(evaluate_submission, result_id, timeout=timeout)


def get_relevant_submissions(person, project):
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
        result = Result(submission=submission)
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
