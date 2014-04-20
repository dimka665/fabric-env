# coding=utf8

import os
import re
import inspect
import types

import fabric
import fabric.api
import fabric.colors


class memoize():

    def __init__(self, function):
        self.function = function
        self.last_result = None

    def __call__(self, *args, **kwargs):
        if self.last_result:
            return self.last_result
        else:
            result = self.function(*args, **kwargs)
            self.last_result = result
            return result


# --- Variables ---

def get_var(var_name=None):
    if os.path.isfile('fabric.ini'):
        from ConfigParser import SafeConfigParser
        config_parser = SafeConfigParser()
        config_parser.read('fabric.ini')
        vars = dict(config_parser.items('main'))
    else:
        vars = {}

    return vars.get(var_name, None) if var_name else vars


def set_var(var_name, var_value):
    from ConfigParser import SafeConfigParser
    config_parser = SafeConfigParser()
    config_parser.read('fabric.ini')

    if not config_parser.has_section('main'):
        config_parser.add_section('main')

    config_parser.set('main', var_name, var_value)
    config_parser.write(open('fabric.ini', 'w'))


# --- Input/Output ---

icolor = fabric.colors.cyan  # color for interactive


def humanize(var_name):
    return var_name.replace('_', ' ').capitalize()


def input_lacking_vars(template, format_kwargs):
    vars = get_var()
    vars.update(format_kwargs)

    template_vars = re.findall('[^{]{(\w+)}[^}]', template)
    # print(template_vars)
    entered_vars = {}
    for var_name in template_vars:
        if var_name not in vars:
            var_value = ensure_prompt(humanize(var_name))
            entered_vars[var_name] = var_value
            set_var(var_name, var_value)

    vars.update(entered_vars)
    return vars


# def var_format(template, *args, **format_kwargs):
#     format_kwargs = input_lacking_vars(template, format_kwargs)
#     output = template.format(*args, **format_kwargs)
#     return output


# def var_format(func):
def var_format_decorator(func):
    if isinstance(func, types.FunctionType):
        arg_spec = inspect.getargspec(func)
    else:
        arg_spec = inspect.getargspec(func.func)

    # args, varargs, varkw = inspect.getargs(func.func_code)

    if arg_spec.defaults:
    # if func.func_defaults:
    #     func_kwargs_names = args[-len(func.func_defaults):]
        func_kwargs_names = arg_spec.args[-len(arg_spec.defaults):]
    else:
        func_kwargs_names = {}

    def inner(template, *args, **kwargs):
        func_kwargs = {}
        for func_kwarg_name in func_kwargs_names:
            if func_kwarg_name in kwargs:
                func_kwargs[func_kwarg_name] = kwargs.pop(func_kwarg_name)

        format_kwargs = input_lacking_vars(template, kwargs)
        output = template.format(*args, **format_kwargs)
        return func(output, **func_kwargs)

    return inner


# def var_format_decorator(function):
#     def inner(template, *args, **format_kwargs):
#         kwargs = format_kwargs.pop('kwargs', {})
#         format_kwargs = input_lacking_vars(template, format_kwargs)
#         output = template.format(*args, **format_kwargs)
#         return function(output, **kwargs)
#     return inner


@var_format_decorator
def prompt(message):
    # message = var_format(message)
    return fabric.api.prompt(icolor('  ' + message))  # spaces inside color to avoid strip


@var_format_decorator
def ensure_prompt(message):
    if not message.endswith(':'):
        message += ':'

    entered = ''
    while not entered:
        entered = fabric.api.prompt(icolor('  ' + message))  # spaces inside color to avoid strip
    return entered


@var_format_decorator
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


@var_format_decorator
def choose(message, options=[]):
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


# class Printer():
#     def __int__(self, color):
#         self.color = color
#
#     def __call__(self, message):
#         message = var_format(message)
#         print_color(message, self.color)


@var_format_decorator
def info(message):
    print_color(message, fabric.colors.blue)

@var_format_decorator
def success(message):
    print_color(message, fabric.colors.green)

@var_format_decorator
def warning(message):
    print_color(message, fabric.colors.yellow)

@var_format_decorator
def error(message):
    print_color(message, fabric.colors.red)


# info = Printer(fabric.colors.blue)
# error = Printer(fabric.colors.red)
# warning = Printer(fabric.colors.yellow)
# success = Printer(fabric.colors.green)

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
    # chosen = choose(message, kwargs={'options': function_dict.keys()})
    chosen = choose(message, options=function_dict.keys())
    return function_dict[chosen]()


# -- Deprecated --
# todo ???
def task(task_function):
    task_function.__name__ = task_function.__name__.replace('_', '-')
    return fabric.api.task(task_function)
