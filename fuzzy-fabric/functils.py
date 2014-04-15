# coding=utf8

import fabric
from fabric.colors import cyan, green, yellow, red, blue


# --- Input/Output ---
icolor = cyan  # color for interactive

def format(self, template, *args, **kwargs):
    self_dict = self.__dict__.copy()
    self_dict.update(kwargs)
    self_dict['root'] = self.root
    return template.format(*args, **self_dict)

def format_message(function):
    return function

@format_message
def prompt(message):
    return fabric.api.prompt(icolor('  ' + message))  # spaces inside cyan to cancel trim

@format_message
def ensure_prompt(message):
    entered = ''
    while not entered:
        entered = fabric.api.prompt(icolor('  ' + message))  # spaces inside cyan to cancel trim
    return entered

@format_message
def confirm(message='Sure?'):
    return fabric.api.prompt(icolor('  ' + message + " ('yes' to confirm)")) == 'yes'

def choose(message, options):
    # print options
    options.sort(key=str.lower)
    info('\n  '.join(options), icolor)
    info('')
    while True:
        entered = fabric.api.prompt(icolor('  ' + message))
        if len(entered) >= 2:
            suited = filter(lambda x: x.lower().startswith(entered), options)
            if len(suited) == 1:
                return suited[0]

@format_message
def info(message, color=blue):
    print('  ' + color(message))

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

def set_name(func_name):
    """
    Decorator for setting name to function
    """
    def set_name_inner(func):
        func.__name__ = func_name
        return func

    return set_name_inner


def call_choosen(message='Execute:', *funcs):
    funcs_dict = {func.__name__: func for func in funcs}
    choosen = choose(message, funcs_dict.keys())
    return funcs_dict[choosen]()


# -- Deprecated --
# todo ???
def task(task_function):
    task_function.__name__ = task_function.__name__.replace('_', '-')
    return fabric.decorators.task(task_function)
