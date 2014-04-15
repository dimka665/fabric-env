__author__ = 'dimka'

import unittest

from fabric_env.utils import Environment2 as Environment
from fabric_env.utils import environment2 as environment
from fabric_env.utils import task
# from fuzzy-fabric.tests.fabfile import *


@task
def get_name():
    return environment.name


class EnvironmentCase(unittest.TestCase):
    # def setUp(self):
    #     self.env_1 = environment('1')
    #     self.env_2 = environment('2')

    def test_swith_to_first_instance(self):
        self.assertEqual(get_name(), 'default')

        # print(environment.name)
        print ' ---------------- BEFORE ' + environment._instance.name
        env_2 = Environment('2')
        print ' ---------------- AFTER ' + environment._instance.name
        # print(environment._instance.name)
        self.assertEqual(get_name(), 'default')

        environment.set_one(env_2)
        self.assertEqual(get_name(), '2')


    def test_tags(self):
        pass


if __name__ == '__main__':
    unittest.main()
