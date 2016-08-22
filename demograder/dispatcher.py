from collections import defaultdict
from itertools import product
from os.path import basename, dirname, join as join_path
from shutil import copyfile
from tempfile import TemporaryDirectory
from textwrap import dedent
from subprocess import run as run_process, PIPE, TimeoutExpired

import django_rq

from .models import Result, ResultDependency

DISPATCH_QUEUE = Queue('dispatch', connection=redis_conn)
EVALUATION_QUEUE = Queue('evaluation', connection=redis_conn)

DGLIB = join_path(dirname(__file__), 'dglib.py')

TIMEOUT_LIMIT = 10 # seconds

def evaluate_submission(script, uploads, result, kwargs):
    _setup_django()
    # create temporary directory
    with TemporaryDirectory() as temp_dir:
        # copy dglib library
        tmp_dglib = copyfile(DGLIB, join_path(temp_dir, basename(DGLIB)))
        # copy the submission script
        tmp_script = copyfile(script, join_path(temp_dir, basename(script)))
        # copy the submission
        tmp_uploads = []
        for upload in uploads:
            tmp_uploads.append(copyfile(upload, join_path(temp_dir, basename(upload))))
        # copy all dependency files
        tmp_args = defaultdict(list)
        for key, submission in kwargs.items():
            for upload in submission.upload_set.all():
                filepath = upload.file.name
                tmp_args[key].append(copyfile(filepath, join_path(temp_dir, basename(filepath))))
        try:
            args = ['--_script', tmp_script, '--_uploads', ','.join(tmp_uploads)]
            for key, files in tmp_args.items():
                args.extend(('--{}'.format(key), ','.join(files)))
            # FIXME switch user
            args = ['python3.5', tmp_dglib] + args
            completed_process = run_process(args, timeout=TIMEOUT_LIMIT, stderr=PIPE, stdout=PIPE)
            stdout = completed_process.stdout.decode('utf-8')
            stderr = completed_process.stderr.decode('utf-8')
            return_code = completed_process.returncode
        except TimeoutExpired as e:
            stdout = e.stdout.decode('utf-8')
            stdout += '\n\n' +  dedent('''
            The program failed to complete within {}
            seconds and was terminated.
            '''.format(TIMEOUT_LIMIT)).strip()
            stderr = e.stderr.decode('utf-8')
            return_code = 1
    # update Result
    result.stdout = stdout.strip()
    result.stderr = stderr.strip()
    result.return_code = return_code
    result.save()

def dispatch_submission(submission):
    _setup_django()
    student = submission.student
    project = submission.project
    if not project.script:
        return
    # space is a dictionary of lists of Submissions
    space = defaultdict(list)
    # for each project dependency
    for project_dependency in project.projectdependency_set.all():
        # FIXME 
        if project_dependency.dependency_structure == ProjectDependency.SELF:
            space[project_dependency.keyword].extend(tuple(student.submissions.filter(project=project_dependency.producer)))
        elif project_dependency.dependency_structure == ProjectDependency.INSTRUCTOR:
            space[project_dependency.keyword].extend(tuple(proejct.course.instructor.submissions.filter(project=project_dependency.producer)))
        elif project_dependency.dependency_structure == ProjectDependency.CLIQUE:
            for classmate in project.course.enrolled_students
            pass
        elif project_dependency.dependency_structure == ProjectDependency.CUSTOM:
            # for each pair of students matched
            for student_dependency in project_dependency.studentdependency_set.filter(student=submission.student):
                # add all submissions as arguments
                space[project_dependency.keyword].extend(tuple(student_dependency.producer.submissions.filter(project=project_dependency.producer)))
    keys = sorted(space.keys())
    script = project.script.name
    uploads = tuple(upload.file.name for upload in submission.upload_set.all())
    for dependencies in product(*(space[key] for key in keys)):
        kwargs = dict(zip(keys, dependencies))
        result = Result(
            submission=submission,
        )
        result.save()
        for upstream_submission in kwargs.values():
            ResultDependency(
                result=result,
                producer=upstream_submission,
            ).save()
        EVALUATION_QUEUE.enqueue(evaluate_submission, script, uploads, result, kwargs)

def enqueue_submission_dispatch(submission):
    DISPATCH_QUEUE.enqueue(dispatch_submission, submission)

def _setup_django():
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangosite.settings")
    import django
    django.setup()
