# coding=utf8

import os
import string

from fabric.context_managers import settings
from fabric.api import env    # for import from upper fabfile
from fabric.operations import run, local

# from fuzzy-fabric.utils import Environment, split_requirements

from fabric_env.functils import *

# environment = Environment('default')

# --- Variables ---

def var(var_name):
    if not os.path.isfile('fabric.ini'):
        return None if var_name else {}

    from ConfigParser import SafeConfigParser

    config_parser = SafeConfigParser()
    config_parser.read('fabric.ini')

    if var_name:
        return config_parser.get('main', var_name)
    else:
        return dict(config_parser.items('main'))

# --- Init ---

def template_path(path):
    """
    Returns absolute path to 'path' template
    """
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    return os.path.join(template_dir, path)


def copy_and_fill(file_rel_path, **kwargs):
    """
    Copy file from templates to project and substitute variables
    """
    file_abs_path = template_path(file_rel_path)
    template_string = open(file_abs_path).read().decode('utf8')

    template = string.Template(template_string)
    content = template.safe_substitute(kwargs)

    open(file_rel_path, 'w').write(content)


# @set_name('project')
# def init_project():
#     name = prompt('Project name:')
#     copy_and_fill('fabric.ini', name=name)
#     if os.path.isfile('fabric.ini'):
#         success("'fabric.ini' was created")
#     else:
#         error("'fabric.ini' was not created")


def fabric(name=None):
    if os.path.isfile('fabric.ini'):
        return error("'fabric.ini' exists already")

    name = name or ensure_prompt('Project name:')
    copy_and_fill('fabric.ini', name=name)

    if os.path.isfile('fabric.ini'):
        success("'fabric.ini' was created")
    else:
        error("'fabric.ini' was not created")


@set_name('setup.py')
def init_setup():
    """
    Creates 'setup.py' from template
    """
    if os.path.isfile('setup.py'):
        return error("'setup.py' already exists")

    name = var('name') or ensure_prompt('Project name:')
    copy_and_fill('setup.py', name=name)

    if os.path.isfile('setup.py'):
        success("'setup.py' was created")
    else:
        error("'setup.py' was not created")


@set_name('README.rst')
def init_readme():
    name = prompt('Project name:')
    info("Creating 'fabric.ini'...")
    copy_and_fill('fabric.ini', name=name)
    if os.path.isfile('fabric.ini'):
        success("'fabric.ini' was created")
    else:
        error("'fabric.ini' was not created")


@set_name('nginx')
def init_nginx():
    pass


@task
def init():
    """
    fabric/setup.py/README/...
    """
    return call_choosen('Init:',
        init_setup,
        init_readme,
        fabric,
        # init_nginx,
        # init_uwsgi,
        # init_gitignore,
        # init_hgignore,
    )

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


# # --- pip ---
# # todo когда устанавливаем новое окружение то пакеты устанавливают старые зависимости, а нам нужны новые версии
# # todo например, django-lfs устанавливает старый django-compressor==1.1.1 Нам нужен ==1.2
# @task
# def install(*packages, **kw_packages):
#     """
#     pip install
#     """
#     if environment.editable:
#         environment('pip install --editable ' + packages[0])
#         return None
#
#     params = ''
#     if environment.force:
#         params += ' --force-reinstall'
#
#
#     if environment.cache:
#         params += ' --download-cache=' + environment.root.pip_cache
#
#     for package in packages:
#         environment.env('pip install {package} {params}', package=package, params=params)
#
#     for package, version in kw_packages.items():
#         if version:
#             package_version = package + '==' + version
#             environment.env('pip install {package} {params}', package=package_version, params=params)
#         else:
#             environment.env('pip install --upgrade {package} {params}', package=package, params=params)


@task
def uninstall(package):
    """
    pip uninstall
    """
    environment.env('pip uninstall ' + package)


@task
def pip_update_requirements(no_deps=''):
    """
    pip_update_requirements('no-deps') - установить без зависимостей
    pip_update_requirements()          - установить с зависимостями
    """
    command = 'pip install --requirement={root.requirements.common} --requirement={root.requirements.private} --download-cache={root.pip_cache}'

    if no_deps:
        command += ' --no-deps'

    with environment.virtualenv():
        environment(command)


@task
def freeze():
    """
    pip freeze
    """
    environment.env('pip freeze')


# todo доделать
def splitreqs():
    with environment.virtualenv():
        requirements = environment.root.temp + 'requirements.txt'
        # requirements.mkfile()
        # environment('pip freeze --local > ' + requirements)
        environment('pip freeze > ' + str(requirements))
        # environment('pip freeze > ' + requirements)
        split_requirements(requirements, environment)


# -- VCS ---
def repo_init():
    if environment.hg:
        hg_init()
    elif environment.git:
        git_init()
    else:
        environment.error("No repo init. Choose VCS at 'fabfile.py'")


def hg_init():
    environment('hg init')


def git_init():
    pass


@task
def hg():
    """
    hg [init/pull/push/commit/...]
    """
    environment.hg = True


@task
def status():
    """
    [hg/git] status
    """
    if environment.hg:
        result = hg_status()
    elif environment.git:
        result = git_status()
    else:
        # environment.error('')
        return False


def hg_status():
    with settings(warn_only=True):
        result = environment('hg status').succeeded
    return result


def git_status():
    pass


def git_addremove():
    pass


@task
def addremove():
    """
    [hg/git] addremove
    """
    if environment.hg:
        hg_addremove()
    elif environment.git:
        git_addremove()
    else:
        environment.error('No repo')


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
    splitreqs()
    addremove()
    commit()
    push()


def project_deploy():
    remote()
    pull()
    update()
    pip_update_requirements('no-deps')
    collectstatic()
    restart()

# =================================================
@task
def deploy_djangobb_save():
    djangobb()
    # pull()

    djangobb_branch = djangobb('hg branch', capture=True)
    # djangobb_branch = djangobb('hg branch')
    if djangobb_branch != 'sdev':
        return error('Чтобы продолжить должна быть выбрана ветка sdev. Сейчас же - ' + djangobb_branch)

    # run('hg branch sdev')
    addremove()
    commit()
    run('hg update sstable')
    run('hg merge sdev')
    commit('merge sdev')
    run('hg update sdev')
    push()


@task
def deploy_djangobb_load():
    djangobb()
    remote()
    pull()
    update('sstable')
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


def git_pull():
    pass


@task
def pull():
    """
    [hg/git] push
    """
    if environment.hg:
        hg_pull()
    elif environment.git:
        git_pull()


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

