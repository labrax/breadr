
import unittest

import crumb

class TestInputErrors(unittest.TestCase):
    def test_definition_missing_input(self):
        def _test():
            @crumb.crumb(output=int)
            def func(valid):
                return None
        self.assertRaises(ValueError, _test)

    def test_definition_but_not_in_params(self):
        def _test():
            @crumb.crumb(input='invalid', output=None)
            def func(valid):
                return None
        self.assertRaises(ValueError, _test)

    def test_definition_but_no_params(self):
        def _test():
            @crumb.crumb(input='invalid', output=None)
            def func():
                return None
        self.assertRaises(ValueError, _test)

    def test_definition_missing(self):
        def _test():
            @crumb.crumb(output=None)
            def func(valid):
                return None
        self.assertRaises(ValueError, _test)

    def test_definition_missing_output(self):
        def _test():
            @crumb.crumb()
            def func(valid):
                return None
        self.assertRaises(TypeError, _test)

if __name__ == '__main__':
    unittest.main()