import sys
from ast import parse
from contextlib import redirect_stdout
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec
from io import StringIO
from os.path import basename
from subprocess import run as run_process, PIPE
from textwrap import dedent

def _multiline_diff(expected, actual):
    different = False
    for line in expected.splitlines():
        line = line.strip()
        actual = actual.strip()
        if not actual.startswith(line):
            different = True
            break
        actual = actual[len(line):]
    return different or actual.strip() != ''

def syntax_test():
    submission = sys.argv[1]
    source = ''
    with open(submission) as fd:
        source = fd.read()
    try:
        parse(source, filename=submission)
        print_result('Submission is valid Python file.', True, should_exit=True)
    except SyntaxError as e:
        print_result('Submission has Python syntax errors: ' + str(e), False, should_exit=True)

def module_test(module):
    stdout = StringIO()
    with redirect_stdout(stdout):
        import_module(module)
    actual_output = stdout.getvalue()
    passed = (actual_output == '')
    if passed:
        print_result('Module imports cleanly.', passed, should_exit=True)
    else:
        transcript = dedent('''
        Importing module results in unexpected prints.
        Printouts are marked within '>>>' and '<<<':

        >>>{}<<<
        ''').strip().format(actual_output)
        print_result(transcript, passed, should_exit=True)

def function_test(fn, arguments, expected_return, expected_output=''):
    template = dedent('''
    FUNCTION CALL
    -------------
    {}

    EXPECTED RETURN VALUE
    ---------------------
    {}

    ACTUAL RETURN VALUE
    -------------------
    {}

    EXPECTED PRINT OUTPUT
    ---------------------
    {}

    ACTUAL PRINT OUTPUT
    -------------------
    {}
    ''').strip()
    multiple_arguments = repr(arguments).startswith('(')
    if multiple_arguments:
        template_input = '{}{}'.format(fn.__name__, repr(arguments))
    else:
        template_input = '{}({})'.format(fn.__name__, repr(arguments))
    template_expected_return = repr(expected_return)
    actual_output = StringIO()
    with redirect_stdout(actual_output):
        try:
            if multiple_arguments:
                actual_return = fn(*arguments)
            else:
                actual_return = fn(arguments)
            template_actual_return = repr(actual_return)
            error = False
        except Exception as e:
            actual_return = None
            template_actual_return = str(e)
            error = True
    actual_output = actual_output.getvalue()
    transcript = template.format(
            template_input,
            template_expected_return,
            template_actual_return,
            expected_output,
            actual_output)
    passed = (not error and
            expected_return == actual_return and
            not _multiline_diff(expected_output, actual_output))
    print_result(transcript, passed, should_exit=True)

def input_output_test(in_str, out_str):
    template = dedent('''
    INPUT
    -----
    {}

    EXPECTED OUTPUT
    ---------------
    {}

    ACTUAL OUTPUT
    -------------
    {}
    ''').strip()
    submission = sys.argv[1]
    input_text = dedent(in_str).strip()
    expected_output = dedent(out_str).strip()
    completed = run_process(['python3.5', submission], input=input_text, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    actual_output = (completed.stdout.strip() + '\n' + completed.stderr.strip()).strip()
    transcript = template.format(input_text, expected_output, actual_output)
    print_result(transcript, completed.returncode == 0 and not _multiline_diff(expected_output, actual_output), should_exit=True)

def print_result(transcript, passed, should_exit=False):
    print(transcript.strip())
    if should_exit:
        if passed:
            exit(0)
        else:
            exit(1)

def shell_adaptor():
    args = sys.argv[1:]
    kwargs = {}
    for i in range(int(len(args) / 2)):
        kwargs[args[2 * i][2:]] = list(args[2 * i + 1].split(','))
    script = kwargs['_script'][0]
    spec = spec_from_file_location(basename(script)[:-3], script)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    module.run(**kwargs)

if __name__ == '__main__':
    shell_adaptor()
