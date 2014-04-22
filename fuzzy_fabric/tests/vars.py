
import unittest

from fuzzy_fabric.utils import Vars


class VarsTestCase(unittest.TestCase):

    def test_vars(self):
        vars = Vars()

        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
