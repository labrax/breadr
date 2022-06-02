
import unittest

from crumb import crumb, CrumbRepository

class TestBasics(unittest.TestCase):
    def test_crumb(self):
        CrumbRepository().reset()

        @crumb(output=int, name='func_test')
        def func(aa=3):
            return aa
        self.assertIn('func_test', CrumbRepository().crumbs)
        self.assertNotIn('func', CrumbRepository().crumbs)
    