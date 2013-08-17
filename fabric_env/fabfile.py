# coding=utf8

import shutil
# from fabric.operations import local
from fabric.context_managers import settings

# import fabric

from fabric.api import prompt
from fabric_env.path import Path
from fabric_env.utils import Environment, split_requirements
from fabric_env.utils import envi
import os

environment = envi

from fabric.decorators import task as f_task
from fabric_env.utils import task


# --- tags ---
@task
def force():
    """force [install]"""
    environment.force = True


@task
def venv():
    """env [init/delete]"""
    environment.venv = True


@task
def nocache():
    """nocache [install]"""
    environment.cache = False


@task
def editable():
    """
    editable [install]
    """
    environment.editable = True


@task
def nginx():
    """
    nginx [deploy]
    """
    environment.nginx = True


@task
def wsgi():
    """
    wsgi [deploy]
    """
    environment.wsgi = True


@task
def fake():
    """
    fake [migrate]
    """
    environment.fake = True


# --- common ---
@task
def init():
    """[project/env/hg/git] init"""
    if environment.venv:
        env_init()
    elif environment.hg:
        hg_init()
    elif environment.git:
        git_init()
    else:
        project_init()


@task
def delete():
    """[env] delete"""
    if environment.env:
        env_delete()


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


def project_init_copy():
    # todo убрать python
    templates = Path.rel(__file__, '../templates/') + 'python'
    files = ['README.rst', 'setup.py', '.hgignore', '.gitignore']

    for file_ in files:
        template = open(templates / file_).read().decode('utf8')
        content = template.format(name=environment.name)
        open(environment.root / file_, 'w').write(content)


# --- virtualenv ---
def env_init():
    if environment.confirm('Создать виртуальное окружение?'):
        environment('virtualenv --distribute {root.env}')  # --distribute install distribute


def env_delete():
    if environment.confirm("Удалить виртуальное окружение '{root.env}'?"):
        environment('rm -rf {root.env}')


@task
def activate():
    """
    <not work>
    """
    pass


# --- pip ---
# todo когда устанавливаем новое окружение то пакеты устанавливают старые зависимости, а нам нужны новые версии
# todo например, django-lfs устанавливает старый django-compressor==1.1.1 Нам нужен ==1.2
@task
def install(*packages, **kw_packages):
    """
    pip install
    """
    params = ''
    if environment.force:
        params += ' --force-reinstall'

    if environment.editable:
        packages = ' --editable'

    if environment.cache:
        params += ' --download-cache=' + environment.root.pip_cache

    for package in packages:
        environment.env('pip install {package} {params}', package=package, params=params)

    for package, version in kw_packages.items():
        if version:
            package_version = package + '==' + version
            environment.env('pip install {package} {params}', package=package_version, params=params)
        else:
            environment.env('pip install --upgrade {package} {params}', package=package, params=params)


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


@task
def deploy():
    """
    [project/nginx/wsgi] deploy
    """
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
    if environment('hg pull {hg_server}').succeeded:
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
    if environment('hg push {hg_server}'):
        environment.success('Pushed')
    else:
        environment.error('Push failed')


def git_push():
    if environment('git-push {git_server}'):
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
    environment.env('./manage.py collectstatic --noinput')
    environment.success('Static collected')


@task
def syncdb():
    """
    manage.py syncdb
    """
    environment.env('./manage.py syncdb')

@task
def migrate(app_name):
    """
    [fake] manage.py migrate [...]
    """
    params = '--fake ' if environment.fake else ''
    environment.env('./manage.py ' + params + app_name)


def hg_commit(message=''):
    if not message:
        message = prompt('Commit message: ')

    if message:
        if environment('hg commit -m "{message}"', message=message).succeeded:
            environment.success('Commited')
    else:
        environment.error('Commit failed')


def git_commit(message=''):
    pass


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

