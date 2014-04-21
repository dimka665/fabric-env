# coding=utf8
import functools

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
# todo to cache on get and set
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

    # take format token from template
    # e.g., 'package_name' from 'Init {package_name}?'
    template_vars = re.findall('(?!<[^{]){(\w+)}(?![^}])', template)
    entered_vars = {}
    for var_name in template_vars:
        if var_name not in vars:
            var_value = ensure_prompt(humanize(var_name))
            entered_vars[var_name] = var_value
            set_var(var_name, var_value)

    vars.update(entered_vars)
    return vars


def var_format(func):

    if isinstance(func, functools.partial):
        func = func.func

    func_kwargs_names = {}
    argspec = inspect.getargspec(func)
    if argspec.defaults:
        func_kwargs_names = argspec.args[-len(argspec.defaults):]

    def inner(template, *args, **kwargs):
        func_kwargs = {}
        for func_kwarg_name in func_kwargs_names:
            if func_kwarg_name in kwargs:
                func_kwargs[func_kwarg_name] = kwargs.pop(func_kwarg_name)

        format_kwargs = input_lacking_vars(template, kwargs)
        output = template.format(*args, **format_kwargs)
        return func(output, **func_kwargs)

    return inner


def var_format_message(template, *args, **kwargs):
    format_kwargs = input_lacking_vars(template, kwargs)
    return template.format(*args, **format_kwargs)


@var_format
def prompt(message):
    # message = var_format(message)
    return fabric.api.prompt(icolor('  ' + message))  # spaces inside color to avoid strip


@var_format
def ensure_prompt(message):
    if not message.endswith(':'):
        message += ':'

    entered = ''
    while not entered:
        entered = fabric.api.prompt(icolor('  ' + message))  # spaces inside color to avoid strip
    return entered


@var_format
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


@var_format
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


@var_format
def info(message):
    print_color(message, fabric.colors.blue)

@var_format
def success(message):
    print_color(message, fabric.colors.green)

@var_format
def warning(message):
    print_color(message, fabric.colors.yellow)

@var_format
def error(message):
    print_color(message, fabric.colors.red)


def func_repr(func):
    if isinstance(func, functools.partial):
        func = func.func

    if func.__doc__:
        return func.__doc__.strip()
    else:
        return func.__name__


def call_chosen(funcs, message='Execute'):
    func_dict = {func_repr(func): func for func in funcs}
    chosen = choose(message, options=func_dict.keys())
    return func_dict[chosen]()


# -- Deprecated --
# todo ???
def task(task_function):
    task_function.__name__ = task_function.__name__.replace('_', '-')
    return fabric.api.task(task_function)
