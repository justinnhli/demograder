import sys
from os import execvp

def run(**kwargs):
    # FIXME assumes a test file exists
    # which may not be the case if there are no student dependencies
    test_file = kwargs['test'][0]
    upload = kwargs['_uploads'][0]
    execvp(sys.executable, (sys.executable, '-B', test_file, upload,))
