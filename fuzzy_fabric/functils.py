# coding=utf8

import fabric
import fabric.api
import fabric.colors

# --- Input/Output ---

icolor = fabric.colors.cyan  # color for interactive


def format_message(function):
    def inner(message, *args, **kwargs):
        message = message.format(*args, **kwargs)
        return function(message)
    return inner


@format_message
def prompt(message):
    return fabric.api.prompt(icolor('  ' + message))  # spaces inside color to avoid strip


@format_message
def ensure_prompt(message):
    entered = ''
    while not entered:
        entered = fabric.api.prompt(icolor('  ' + message))  # spaces inside color to avoid strip
    return entered


@format_message
def confirm(message='Are you sure?'):
    return fabric.api.prompt(icolor('  ' + message)) == 'yes'


def suited_options(options, entered):
    result = []
    for option in options:
        handy_for_input_option = option.lstrip(' .-').lower()
        if handy_for_input_option.startswith(entered):
            result.append(option)
    return result


def print_color(message, color=fabric.colors.blue):
    print('  ' + color(message))


def choose(message, options):
    # print options
    options.sort(key=str.lower)
    print_color('\n  '.join(options), icolor)
    print_color('')
    while True:
        entered = fabric.api.prompt(icolor('  {}:'.format(message)))
        if len(entered) >= 2:
            suited = suited_options(options, entered)
            if len(suited) == 1:
                return suited[0]


@format_message
def info(message):
    print_color(message, fabric.colors.blue)

@format_message
def success(message):
    print_color(message, fabric.colors.green)

@format_message
def warning(message):
    print_color(message, fabric.colors.yellow)

@format_message
def error(message):
    print_color(message, fabric.colors.red)

# --- Tasks ---

# def set_name(func_name):
#     """
#     Decorator for setting name to function
#     """
#     def set_name_inner(func):
#         func.__name__ = func_name
#         return func
#
#     return set_name_inner


def function_repr(function):
    if function.__doc__:
        return function.__doc__.strip()
    else:
        return function.__name__


def call_chosen(functions, message='Execute'):
    function_dict = {function_repr(function): function for function in functions}
    chosen = choose(message, function_dict.keys())
    return function_dict[chosen]()


# -- Deprecated --
# todo ???
def task(task_function):
    task_function.__name__ = task_function.__name__.replace('_', '-')
    return fabric.api.task(task_function)
