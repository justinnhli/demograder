from collections import defaultdict
from itertools import product
from os.path import basename, dirname, join as join_path
from shutil import copyfile
from tempfile import TemporaryDirectory
from textwrap import dedent
from subprocess import run as run_process, PIPE, TimeoutExpired

import django_rq

from .models import Result, ResultDependency

DGLIB = join_path(dirname(__file__), 'dglib.py')

TIMEOUT_LIMIT = 10 # sections

def evaluate_submission(script, uploads, result, kwargs):
    # create temporary directory
    with TemporaryDirectory() as temp_dir:
        # copy dglib library
        tmp_dglib = copyfile(DGLIB, join_path(temp_dir, basename(DGLIB)))
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
            args = ['--_script', script, '--_uploads', ','.join(tmp_uploads)]
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
    project = submission.project
    if not project.script:
        return
    # space is a dictionary of lists of Submissions
    space = defaultdict(list)
    # for each project dependency
    for project_dependency in project.projectdependency_set.all():
        # for each pair of students matched
        for student_dependency in project_dependency.studentdependency_set.filter(student=submission.student):
            # add all submissions as arguments
            space[project_dependency.keyword].extend(tuple(student_dependency.producer.submission_set.filter(project=project_dependency.producer)))
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
        django_rq.enqueue(evaluate_submission, script, uploads, result, kwargs)
