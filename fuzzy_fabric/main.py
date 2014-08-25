
import os
import sys

from fabric.main import main as fabric_main
from fabric.main import parse_options


fabfile = os.path.join(os.path.dirname(__file__), 'fabfile.py')


def extract_commands():
    parser, fabric_options, commands = parse_options()

    for ff_command in commands:
        sys.argv.remove(ff_command)

    fabric_command = '{}:{}'.format(commands[0], ','.join(commands[1:]))
    sys.argv.append(fabric_command)


def main():
    args_count = len(sys.argv) - 1

    # 'ff'  =>  'fab --list'
    if args_count == 0:
        sys.argv.append('--list')

    # 'ff command arg1 arg2'  =>  'fab command:arg1,arg2'
    elif args_count > 1:
        extract_commands()

    return fabric_main([fabfile])
