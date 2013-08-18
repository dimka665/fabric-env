
from fabric_env.fabfile import *


# environment.root_from(__file__)
environment.root = Path.rel(__file__)
environment.hg_path = 'git+ssh://git@github.com/dimka665/fabric-env.git'


@task
def test():
    print('--== ' + 'test' + ' ==--')