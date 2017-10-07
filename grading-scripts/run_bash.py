from os import execvp

def run(**kwargs):
    # FIXME assumes a test file exists
    # which may not be the case if there are no student dependencies
    test_file = kwargs['test'][0]
    execvp('bash', ('bash', test_file,))
