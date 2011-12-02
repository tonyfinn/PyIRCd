import unittest
from pprint import pformat

class BasicTestCase(unittest.TestCase):
    def assertAllIn(self, first_list, second_list, msg=None):
        for x in first_list:
            error = "Missing element: {}\n".format(pformat(x))
            if msg != None:
                error = msg + '\n' + error
            error += 'Second contains: ' + '\n' + pformat(second_list)
            self.assertTrue(x in second_list, error)

    def assert_true(self, *args, **kwargs):
        self.assertTrue(*args, **kwargs)

    def assert_false(self, *args, **kwargs):
        self.assertFalse(*args, **kwargs)

    def assert_all_in(self, *args, **kwargs):
        self.assertAllIn(*args, **kwargs)

    def assert_in(self, *args, **kwargs):
        self.assertIn(*args, **kwargs)

    def assert_not_in(self, *args, **kwargs):
        self.assertNotIn(*args, **kwargs)

    def assert_equal(self, *args, **kwargs):
        self.assertEqual(*args, **kwargs)

    def assert_not_equal(self, *args, **kwargs):
        self.assertNotEqual(*args, **kwargs)

    def assert_raises(self, *args, **kwargs):
        self.assertRaises(*args, **kwargs)
