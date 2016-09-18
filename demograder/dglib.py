import sys
from ast import parse
from contextlib import redirect_stdout
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec
from io import StringIO
from os.path import basename
from subprocess import run as run_process, PIPE
from textwrap import dedent

def is_different(expected, actual):
    # note: this function deliberately ignores newlines to deal with input()
    different = False
    for line in expected.splitlines():
        line = line.strip()
        actual = actual.strip()
        if not actual.startswith(line):
            return True
        actual = actual[len(line):]
    return actual.strip() != ''

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

def module_test(module=None):
    if module is None:
        module = basename(sys.argv[1])
    if module.endswith('.py'):
        module = module[:-3]
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

# from http://pylint-messages.wikidot.com/all-codes
LINT_CHECKS = {
    'C0301': 'Line too long (%s/%s)',
    'C0303': 'Trailing whitespace',
    'C0325': 'Unnecessary parens after %r keyword',
    'C0326': '',
    'E0001': 'Syntax error',
    'E0104': 'Return outside function',
    'E0107': 'Use of the non-existent %s operator',
    'E0601': 'Using variable %r before assignment',
    'E0602': 'Undefined variable %r',
    'R0801': 'Similar lines in %s files',
    'W0101': 'Unreachable code',
    'W0102': 'Dangerous default value %s as argument',
    'W0104': 'Statement seems to have no effect',
    'W0120': 'Else clause on loop without a break statement',
    'W0122': 'Use of exec',
    'W0301': 'Unnecessary semicolon',
    'W0311': 'Bad indentation. Found %s %s, expected %s',
    'W0312': 'Found indentation with %ss instead of %ss',
    'W0333': 'Use of the `` operator',
    'W0603': 'Using the global statement',
    'W0611': 'Unused import %s',
    'W0612': 'Unused variable %r',
}

def lint_test():
    from pylint.lint import Run as lint
    file = sys.argv[1]
    actual_output = StringIO()
    with redirect_stdout(actual_output):
        try:
            lint([file, '--disable=all', '--enable=' + ','.join(sorted(LINT_CHECKS.keys())), '--max-line-length=150'])
        except SystemExit:
            pass
    actual_output = actual_output.getvalue().strip()
    passed = (actual_output == '')
    if passed:
        print_result('Coding style okay.', passed, should_exit=True)
    else:
        transcript = dedent('''
        There are some coding style issues; the numbers represent the line and column respectively.

        {}
        ''').strip().format('\n'.join(actual_output.splitlines()[1:]))
        print_result(transcript, passed, should_exit=True)

def function_test(fn, arguments, expected_return, expected_output='', quiet=False, should_exit=True):
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
            not is_different(expected_output, actual_output))
    print_result(transcript, passed, quiet=quiet, should_exit=should_exit)

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
    completed = run_process([sys.executable, submission], input=input_text, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    actual_output = (completed.stdout.strip() + '\n' + completed.stderr.strip()).strip()
    transcript = template.format(input_text, expected_output, actual_output)
    print_result(transcript, completed.returncode == 0 and not is_different(expected_output, actual_output), should_exit=True)

def print_result(transcript, passed, quiet=False, should_exit=False):
    if not quiet:
        print(transcript.strip())
    elif passed:
        print('pass')
    else:
        print(transcript.strip())
        print('FAIL')
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
