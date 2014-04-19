# coding=utf8

import os
import string
from functools import partial

from fabric.api import *

from fuzzy_fabric.functils import *


# decorate local
local = partial(local, shell='/bin/bash')
local = var_format(local)


@task
def test():
    with prefix('source virtualenvwrapper.sh'):
        # local('workon fuzzy-fabric', shell='/bin/bash')  # Works in virtualenv
        local('workon')  # Works in virtualenv



# --- Init ---

def copy_and_fill(file_path, ensure_name=False, **kwargs):
    """
    Copy file from templates to project and substitute variables
    """
    if os.path.isfile(file_path):
        warning("'{}' exists already", file_path)
        if confirm("Rewrite '{}'?", file_path):
            os.remove(file_path)
        else:
            return None

    vars = get_var()
    vars.update(kwargs)

    if 'name' not in vars and ensure_name:
        # vars['name'] = ensure_prompt('Project name:')
        vars['name'] = get_name()

    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    template_path = os.path.join(templates_dir, file_path)
    template_string = open(template_path).read().decode('utf8')

    template = string.Template(template_string)
    content = template.safe_substitute(vars)

    open(file_path, 'w').write(content)

    if os.path.isfile(file_path):
        success("'{}' was wrote", file_path)
    else:
        error("'{}' is not exists", file_path)


def init_setup():
    """
    setup.py
    """
    if confirm('Create setup.py?'):
        copy_and_fill('setup.py', ensure_name=True)
        return True
    return False


def init_readme():
    """
    README.rst
    """
    if confirm('Create README.rst?'):
        copy_and_fill('README.rst')
        return True
    return False


def init_fabric():
    """
    fabric.ini
    """
    if confirm('Create fabric.ini?'):
        copy_and_fill('fabric.ini', ensure_name=True)


def init_hgignore():
    """
    .hgignore
    """
    copy_and_fill('.hgignore')


def init_gitignore():
    """
    .gitignore
    """
    copy_and_fill('.gitignore')


def init_nginx():
    """
    nginx
    """
    pass


@memoize        # In Python3 replace to functools.lru_cache
def get_name():
    name = get_var('name')
    if name:
        return name
    else:
        return ensure_prompt('Project name:')


@memoize        # In Python3 replace to functools.lru_cache
def get_package_name():
    package_name = get_var('package_name')
    if package_name:
        return package_name
    else:
        return get_name().replace('-', '_')


def init_virtualenv(python='python2'):
    if confirm('Create {} virtualenv?', python):
        with prefix('source virtualenvwrapper.sh'):
            local('mkvirtualenv "{}" -a . --python=`which {}`'.format(get_name(), python))
        return True
    return False


def init_git():
    if confirm('git init?'):
        local('git init')
        init_gitignore()
        return True
    return False


def init_hg():
    if confirm('hg init?'):
        local('hg init')
        init_hgignore()
        return True
    return False


def init_package():
    if confirm('Create package?'):
        local('mkdir {package_name}')


def init_all():
    """
    all
    """
    init_fabric()

    if not init_virtualenv('python2'):
        init_virtualenv('python3')

    if not init_git():
        init_hg()

    init_setup()
    init_readme()
    init_package()

@task
def init():
    """
    setup.py/README.rst/fabric.ini/...
    """
    functions = [
        init_all,
        init_setup,
        init_readme,
        init_fabric,
        init_gitignore,
        init_hgignore,

        init_package,
    ]
    return call_chosen(functions, 'Init')


# -----------------------------------------------


# --- project ---
def project_init():
    project_name = prompt('Project name: ')

    if not project_name:
        return

    env_init()
    if environment.confirm('Install Django?'):
        install('django')
        environment.env('python django-admin.py startproject ' + project_name)

    project_init_copy()
    repo_init()
    addremove()
    commit()
    push()


def hg_addremove():
    environment('hg addremove --dry-run')
    if environment.confirm("hg addremove ?"):
        if environment('hg addremove').succeeded:
            environment.success('hg addremove SUCCESS')
        else:
            environment.error('hg addremove FAIL')


# --- setuptools ---
@task
def upload():
    """
    setup.py sdist upload
    """
    environment('python setup.py sdist upload')


# --- Deploy ---
@task
def pd():
    """
    prepare & deploy
    """
    prepare()
    deploy()


@task
def prepare():
    """
    prepare for deploy
    """
    if environment.package:
        package_prepare()
    else:
        project_prepare()


def project_prepare():
    # splitreqs()
    # addremove()
    commit()
    push()


def project_deploy():
    remote()
    pull()
    update()
    # pip_update_requirements('no-deps')
    collectstatic()
    restart()

# =================================================
@task
def ls():
    environment('ls')


def stop():
    fabric.operations

@task
def p(package):
    global environment
    # environment.package = True
    environment.info("swith to {}", package)
    if package in environment.packages:
        environment = environment.packages[package]
        environment.success('Switched to {name}')
        environment.package = True
    else:
        # environment.error("No package '{}'", package)
        fabric.utils.abort(red("No package '{}'".format(package)))


def package_prepare():
    branch = environment('hg branch', capture=True)
    print red(branch)
    if not environment.confirm("Commit to '{branch}'?", branch=branch):
        return
    # if not package.is_dev_branch(branch):
    #     return environment.error("Чтобы продолжить должна быть выбрана ветка sdev. Сейчас выбрана '{}'", branch)
    addremove()
    commit()
    update(environment.stable_branch)
    merge(branch)
    commit('merge ' + branch)
    update(branch)
    push()


def package_deploy(package):
    remote()
    pull()
    update(environment.stable_branch)


def merge(branch=''):
    environment('hg merge ' + branch)


@task
def deploy():
    """
    [project/nginx/wsgi] deploy
    """
    if environment.package:
        return package_deploy()

    if environment.nginx:
        nginx_deploy()
    elif environment.wsgi:
        wsgi_deploy()
    else:
        project_deploy()


def hg_pull():
    if environment('hg pull {hg_path}').succeeded:
        environment.success('hg pull SUCCESS')
    else:
        environment.error('hg pull FAIL')


def hg_update(branch=''):
    if environment('hg update ' + branch).succeeded:
        environment.success("Updated on '{branch}'", branch=branch)
    else:
        environment.error('Update failed')


@task
def update(branch=''):
    """
    [hg/git] update
    """
    if environment.hg:
        hg_update(branch=branch)
    elif environment.git:
        git_update()
    else:
        environment.error('Update failed. No repo.')


def hg_push():
    if environment('hg push {hg_path}').successed:
        environment.success('Pushed')
    else:
        # todo не работает
        environment.error('Push failed')


def git_push():
    if environment('git-push {git_path}'):
        environment.error('Pushed')
    else:
        environment.success('Push failed')


@task
def push():
    """
    [hg/git] push
    """
    if environment.hg:
        hg_push()
    elif environment.git:
        git_push()


def nginx_deploy():
    raise NotImplementedError
    # fabric.api.put(dev.root.config.nginx, '/etc/nginx/sites-enabled/')


def wsgi_deploy():
    raise NotImplementedError
    # fabric.api.put(dev.root.config.uwsgi, '/etc/uwsgi/apps-enabled/')


# --- manage.py ---
@task
def manage(command):
    """
    manage.py [...]
    """
    environment.env('./manage.py ' + command)


@task
def collectstatic():
    """
    manage.py collectstatic --noinput
    """
    environment.env('python manage.py collectstatic --noinput')
    environment.success('Static collected')


@task
def migrate(app_name):
    """
    [fake] manage.py migrate [...]
    """
    params = '--fake ' if environment.fake else ''
    environment.env('./manage.py ' + params + app_name)


def hg_commit(message=''):
    if not message:
        message = environment.prompt('Commit message:')

    if message:
        if environment('hg commit -m "{message}"', message=message).succeeded:
            environment.success('Commited')
    else:
        environment.error('Commit failed')


@task
def commit(message=''):
    """
    [hg/git] commit
    """
    if environment.hg:
        hg_commit(message=message)
    elif environment.git:
        git_commit(message=message)
    else:
        environment.error('Commit failed. No repo.')


@task
def schemamigration(app_name):
    """
    manage.py schemamigration --auto [...]
    """
    environment.env('./manage.py schemamigration --auto ' + app_name)


@task
def remote():
    """
    remote [any command]
    """
    environment.remote = True


@task
def restart():
    """
    restart remote server (uWSGI restart)
    """
    remote()
    environment('/etc/init.d/uwsgi restart')


@task
def shell():
    """
    fabric.operations.open_shell()
    """
    fabric.operations.open_shell()

