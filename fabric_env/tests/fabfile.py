
from fabric_env.fabfile import *
from fabric_env.utils import Environment2 as environment


# environment.hg = True

@task
def get_name():
    return environment.name