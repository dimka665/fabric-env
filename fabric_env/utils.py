# coding=utf-8

import sys
from contextlib import contextmanager

import fabric
from fabric.colors import yellow, red, cyan, green, white, blue
# from fabric.context_managers import prefix, cd, lcd
# from fabric.api import prompt

from fabric_env.path import Path

# def run(command=None, **kwargs):
#     if command:
#         return Environment.current(command, **kwargs)
#     else:
#         return Environment.current

# def environment(*args, **kwargs):
#     return Environment.current(*args, **kwargs)
import os

class Environment0(object):
    pass

class Environment(object):
    # ещё в нём храним состояния
    # tags
    remote = False
    editable = False
    package = False

    _hg = False
    _git = False

    venv = False

    force = False # pip --force-reinstall
    cache = True   # pip --download-cache

    hg_path = ''
    git_path = ''

    # settings
    pip_cache = '~/.pip-cache'
    stable_branch = 'default'

    # utils
    packages = {}

    @property
    def hg(self):
        return self._hg or (not self._git and self.hg_path)
        self('hg status', capture)

    @hg.setter
    def hg(self, value):
        self._hg = value

    @property
    def git(self):
        return self._git or (not self._hg and self.git_path)

    @git.setter
    def git(self, value):
        self._git = value

    def __init__(self, name, root='.', remote_root='.'):
        self.__dict__['_options'] = {}

        self.id = name
        self.name = name

        self.local_root = self.init_root(root)
        self.remote_root = self.init_root(remote_root)

        self.platform = 'linux2'

        # repos
        self.hg_path = ''
        self.git_path = ''

    def init_root(self, root):
        root = Path(root)
        # root.env = 'env'
        root.env = '~/venv'

        root.requirements = 'requirements'
        root.requirements.common = '_common.txt'
        root.requirements.ignore = '_ignore.txt'
        root.requirements.private = '{id}.txt'.format(id=self.id)

        root.config = 'config'
        root.config.nginx = 'nginx.conf'
        root.config.uwsgi = 'uwsgi.ini'

        root.log = 'log'
        root.log.nginx = 'nginx.log'
        root.log.uwsgi = 'uwsgi.log'

        # root.pip_cache = os.path.expanduser('~/.pip-cache')
        # root.temp = '/tmp'
        # root.src = 'src'

        return root

    @property
    def root(self):
        return self.remote_root if self.remote else self.local_root

    @root.setter
    def root(self, value):
        self.local_root = self.init_root(value)

    def root_from(self, file_):
        self.local_root = self.init_root(Path.rel(file_))

    def format(self, template, *args, **kwargs):
        self_dict = self.__dict__.copy()
        self_dict.update(kwargs)
        self_dict['root'] = self.root
        return template.format(*args, **self_dict)

    def __call__(self, command=None, *args, **kwargs):
        command = self.format(command, *args, **kwargs)
        self.info(command)

        if self.remote:
            with fabric.context_managers.cd(self.root):
                return fabric.api.run(command)
        else:
            with fabric.context_managers.lcd(self.root):
                return fabric.api.local(command, capture=True)

    # def capture(self):
    #     pass

    @contextmanager
    def virtualenv(self):
        # path = self.remote_root.env if self.remote else self.root.env
        path = self.root.env
        if self.platform == 'win32':
            prefix_command = path + 'scripts/activate'
        else:
            prefix_command = '. {}'.format(path + 'bin/activate')

        with fabric.context_managers.prefix(prefix_command):
            yield

    @contextmanager
    def env(self, command, *args, **kwargs):
        # root = self.remote_root if self.remote else self.root

        # prefix_command = '. {}'.format(root.env + 'bin/activate')
        prefix_command = '. ' + self.root.env / 'bin/activate'

        # with fabric.context_managers.prefix("'" + prefix_command + "'"):
        with fabric.context_managers.prefix(prefix_command):
            return self(command, *args, **kwargs)

    def activate(self):
        if self.platform == 'win32':
            prefix_command = self.root.env + 'scripts/activate'
        else:
            prefix_command = '. {}'.format(self.root.env + 'bin/activate')
        return prefix_command

    def add_format(function):
        def wrapped(self, template, *args, **kwargs):
            message = self.format(template, *args, **kwargs)
            return function(self, message)
        return wrapped

    @add_format
    def confirm(self, message='Sure?'):
        return fabric.api.prompt(cyan('  ' + message + " ('yes' to confirm)")) == 'yes'

    @add_format
    def info(self, message):
        print('  ' + cyan(message))

    @add_format
    def success(self, message):
        print('  ' + green(message))

    @add_format
    def warning(self, message):
        print('  ' + yellow(message))

    @add_format
    def error(self, message):
        print('  ' + red(message))

    @add_format
    def prompt(self, message):
        return fabric.api.prompt(cyan('  ' + message))    # spaces inside cyan to cancel trim

    @classmethod
    def add_package(cls, package):
        if isinstance(package, cls):
            print('is instance == true')
            cls.packages[package.name] = package


# environment = Environment('default_id')

# class Package():
#     pass

# todo сделать класс Library(repo, location, branch)
def task(task_function):
    task_function.__name__ = task_function.__name__.replace('_', '-')
    return fabric.decorators.task(task_function)


# todo добавить поддержку ссылок и репозиториев, и удаление
def split_requirements(requirements_txt, environment):

    common_packages = read_packages(environment.root.requirements.common)
    env_packages = read_packages(environment.root.requirements.private)
    ignore_packages = read_packages(environment.root.requirements.ignore)

    requirements = read_packages(requirements_txt)

    for name, packages in [('common', common_packages),
                           (environment.id, env_packages),
                           ('depends', ignore_packages)]:
        for package_name in sorted(packages.keys()):
            # если в файле есть пакет с именем установленного пакета
            if package_name in requirements:
                packages[package_name] = requirements.pop(package_name)
                # packages[package_name] = requirements[package_name]
                # del requirements[package_name]
            # если нет, то интересуемся не удалить ли его
            elif fabric.api.prompt("Delete '{}' from '{}'? ('yes' to confirm)".format(package_name, name)) == 'yes':
                del packages[package_name]

    # оставшиеся установленные пакеты
    for package_name in requirements:
        req_name = fabric.api.prompt("Where '{}' to put? (common/{}/ignore) : ".format(package_name, environment.id))
        if req_name == 'ignore':
            ignore_packages[package_name] = requirements[package_name]
        elif req_name == environment.id:
            env_packages[package_name] = requirements[package_name]
        elif req_name == 'common':
            common_packages[package_name] = requirements[package_name]

    write_packages(environment.root.requirements.private, env_packages)
    write_packages(environment.root.requirements.common, common_packages)
    write_packages(environment.root.requirements.ignore, ignore_packages)

# если ссылка, то все норм.

def write_packages(requirements, packages):
    with open(requirements, 'w') as requirements:
        for package_name, line in sorted(packages.items()):
            requirements.writelines([line])


def read_packages(requirements):
    """
    Читаем результат pip freeze
    """
    with open(requirements) as requirements:
        packages = {}
        for line in requirements.readlines():
            # берем все постоянные пакеты
            if not line.startswith('-e'):
                # записываем их по возможности с именами
                package_name = line.split('==')[0]
                packages[package_name] = line
    return packages

