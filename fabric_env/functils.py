# coding=utf8

import fabric
from fabric.colors import cyan, green, yellow, red


# --- Input/Output ---

def format(self, template, *args, **kwargs):
    self_dict = self.__dict__.copy()
    self_dict.update(kwargs)
    self_dict['root'] = self.root
    return template.format(*args, **self_dict)


def format_message(function):
    return function

@format_message
def prompt(message):
    return fabric.api.prompt(cyan('  ' + message))  # spaces inside cyan to cancel trim

@format_message
def confirm(message='Sure?'):
    return fabric.api.prompt(cyan('  ' + message + " ('yes' to confirm)")) == 'yes'

@format_message
def info(message):
    print('  ' + cyan(message))

@format_message
def success(message):
    print('  ' + green(message))

@format_message
def warning(message):
    print('  ' + yellow(message))

@format_message
def error(message):
    print('  ' + red(message))

# --- Tasks ---

def name(func_name):
    """
    Decorator for setting name to function
    """
    def set_name(func):
        func.__name__ = func_name
        return func
    return set_name


# -- Deprecated --
# todo ???
def task(task_function):
    task_function.__name__ = task_function.__name__.replace('_', '-')
    return fabric.decorators.task(task_function)
