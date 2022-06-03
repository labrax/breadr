
import unittest

from crumb import crumb, CrumbRepository
from crumb.base import Slice

cr = CrumbRepository()

class TestBasics(unittest.TestCase):
    def test_crumb(self):
        cr.reset()

        @crumb(output=int, name='func_test')
        def func(aa=3):
            return aa
        self.assertIn('func_test', cr.crumbs)
        self.assertNotIn('func', cr.crumbs)
    
class TestSlice(unittest.TestCase):
    def test_slice(self):
        import math
        import os

        @crumb(output=int, name='a1', deps=[math])
        def func(aa=1):
            return aa
        
        @crumb(output=int, name='a2', deps=os)
        def func(aa=2):
            return aa

        s = Slice(name='first slice')
        s.add_crumb(cr.get_crumb('a1'))
        s.add_crumb(cr.get_crumb('a2'))

        print(s)
        print(s.get_deps())