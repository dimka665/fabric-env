
import os
import sys
from fabric.main import main as fabric_main


# Just 'ff' prints command list
if len(sys.argv) <= 1:
    sys.argv.append('--list')


fabfile = os.path.join(os.path.dirname(__file__), 'fabfile.py')


def main():
    return fabric_main([fabfile])
