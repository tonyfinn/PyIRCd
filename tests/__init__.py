import unittest

class BasicTestCase(unittest.TestCase):
    def assertAllIn(self, first_list, second_list, msg=None):
        for x in first_list:
            msg = msg or "Missing element: {}".format(x)
            self.assertTrue(x in second_list, msg)

    def assert_true(self, *args, **kwargs):
        self.assertTrue(*args, **kwargs)

    def assert_false(self, *args, **kwargs):
        self.assertFalse(*args, **kwargs)

    def assert_all_in(self, *args, **kwargs):
        self.assertAllIn(*args, **kwargs)

    def assert_equal(self, *args, **kwargs):
        self.assertEqual(*args, **kwargs)

    def assert_not_equal(self, *args, **kwargs):
        self.assertNotEqual(*args, **kwargs)
