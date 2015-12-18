from collections import defaultdict
from itertools import product
from os.path import basename, join as join_path
from shutil import copyfile
from tempfile import TemporaryDirectory
from subprocess import run as run_process, PIPE, TimeoutExpired

from redis import Redis
from rq import Queue
import django_rq

SHELL_ADAPTOR = join_path(basename(__file__), 'shell-adaptor.py')

def evaluate_submission(submission, kwargs):
    # create temporary directory
    with TemporaryDirectory() as temp_dir:
        # copy all files
        tmp_args = defaultdict(list)
        for key, files in kwargs.items():
            for filepath in files:
                tmp_args[key].append(copyfile(filepath, join_path(temp_dir, basename(filepath))))
        try:
            args = []
            for key, files in tmp_args.items():
                args.extend(('--{}'.format(key), ','.join(files)))
            # FIXME switch user
            args = ['python3.5', SHELL_ADAPTOR] + args
            # timeout is in seconds (300s == 5min)
            completed_process = run_process(args, timeout=10, stderr=PIPE, stdout=PIPE)
            stdout = completed_process.stdout.decode('utf-8')
            stderr = completed_process.stderr.decode('utf-8')
            return_code = completed_process.returncode
        except TimeoutExpired as e:
            stdout = completed_process.stdout.decode('utf-8')
            stderr = completed_process.stderr.decode('utf-8')
            return_code = e.returncode
    # update db
    submission.stdout = stdout
    submission.stderr = stderr
    submission.return_code = return_code
    submission.save()

def dispatch_submission(student, project, submission):
    if not project.script:
        return
    # space is a dictionary of lists of (lists of files)
    space = defaultdict(list)
    space['_script'].append((project.script.name,))
    space['_submission'].append(tuple(upload.file.name for upload in submission.upload_set.all()))
    # for each project dependency
    for dependency in project.upstream_deps.all():
        # for each pair of students matched
        for match in dependency.match_set.filter(consumer=student):
            # find the producer's submission(s) for the upstream project
            for upstream_sub in dependency.producer.submission_set.filter(student=match.producer):
                # add to dictionary of file arguments
                space[dependency.keyword].append(tuple(upload.file.name for upload in upstream_sub.upload_set.all()))
    keys = sorted(space.keys())
    redis_conn = django_rq.get_connection()
    for files in product(*(space[key] for key in keys)):
        django_rq.enqueue(evaluate_submission, submission, dict(zip(keys, files)))
