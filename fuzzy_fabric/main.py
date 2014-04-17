
import os
from fabric.main import main as fabric_main


fabfile = os.path.join(os.path.dirname(__file__), 'fabfile.py')


def main():
    return fabric_main([fabfile])
