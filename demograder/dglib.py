import sys
from importlib.util import spec_from_file_location, module_from_spec
from os.path import basename
from subprocess import run as run_process, PIPE
from textwrap import dedent

def function_test(fn, arguments, expected):
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
    ''').strip()
    if repr(arguments).startswith('('):
        template_input = '{}{}'.format(fn.__name__, repr(arguments))
    else:
        template_input = '{}({})'.format(fn.__name__, repr(arguments))
    template_expected = repr(expected)
    try:
        actual = fn(*arguments)
        template_actual = repr(actual)
        error = False
    except Exception as e:
        actual = None
        template_actual = str(e)
        error = True
    transcript = template.format(template_input, template_expected, template_actual)
    print_result(transcript, (not error and expected == actual))

def input_output_test(in_str, out_str):
    upload = sys.argv[1]
    input_text = dedent(in_str).strip()
    expected_output = dedent(out_str).strip()
    completed = run_process(['python3.5', upload], input=input_text, stdout=PIPE, universal_newlines=True)
    actual_output = completed.stdout.strip()
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
    transcript = template.format(input_text, expected_output, actual_output)
    passed = False
    for line in expected_output.splitlines():
        line = line.strip()
        actual_output = actual_output.strip()
        if not actual_output.startswith(line):
            break
        actual_output = actual_output[len(line):]
    else:
        passed = True
    print_result(transcript, passed)

def print_result(transcript, passed):
    print(transcript)
    print()
    if passed:
        print('pass')
        exit(0)
    else:
        print('FAIL')
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
