# coding=utf8

import os
import re
import inspect
import functools

import fabric
import fabric.api
import fabric.colors


FUZZY_VARS_FILE = 'fabric.ini'
icolor = fabric.colors.cyan  # color for interactive


class Vars(dict):

    def __getitem__(self, key):
        if key not in self:
            if os.path.isfile(FUZZY_VARS_FILE):
                from ConfigParser import SafeConfigParser
                config_parser = SafeConfigParser()
                config_parser.read(FUZZY_VARS_FILE)

                self.update(config_parser.items('main'))

            if key not in self:
                value = ensure_prompt(humanize(key))
                self[key] = value
                if os.path.isfile(FUZZY_VARS_FILE):
                    config_parser.set('main', key, value)
                    config_parser.write(open(FUZZY_VARS_FILE, 'w'))

        return dict.__getitem__(self, key)


def humanize(var_name):
    return var_name.replace('_', ' ').capitalize()


vars = Vars()


# --- Format ---

def format_decorator(func):

    inspect_func = func
    if isinstance(func, functools.partial):
        inspect_func = func.func

    func_kwargs_names = {}
    argspec = inspect.getargspec(inspect_func)

    if argspec.defaults:
        func_kwargs_names = argspec.args[-len(argspec.defaults):]

    def inner(template, *args, **kwargs):
        func_kwargs = {}
        for func_kwarg_key in func_kwargs_names:
            if func_kwarg_key in kwargs:
                func_kwargs[func_kwarg_key] = kwargs.pop(func_kwarg_key)

        output = format_template(template, *args, **kwargs)
        return func(output, **func_kwargs)

    return inner


def format_template(template, *args, **format_kwargs):
    format_kwargs = get_missed_vars(template, format_kwargs)
    output = template.format(*args, **format_kwargs)
    return output


def get_missed_vars(template, format_kwargs):
    # take format token from template
    # e.g., 'package_name' from 'Init {package_name}?'
    template_var_names = re.findall('(?!<{){(\w+)}(?!})', template)

    for var_name in template_var_names:
        if var_name not in format_kwargs:
            format_kwargs[var_name] = vars[var_name]

    return format_kwargs


# --- Input/Output ---

@format_decorator
def prompt(message):
    return fabric.api.prompt(icolor('  ' + message))  # spaces inside color to avoid strip


@format_decorator
def ensure_prompt(message):
    if not message.endswith(':'):
        message += ':'

    entered = ''
    while not entered:
        entered = fabric.api.prompt(icolor('  ' + message))  # spaces inside color to avoid strip
    return entered


@format_decorator
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


@format_decorator
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


@format_decorator
def info(message):
    print_color(message, fabric.colors.blue)

@format_decorator
def success(message):
    print_color(message, fabric.colors.green)

@format_decorator
def warning(message):
    print_color(message, fabric.colors.yellow)

@format_decorator
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
