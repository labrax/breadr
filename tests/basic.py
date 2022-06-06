
import unittest

from crumb import crumb, CrumbRepository
from crumb.bakery_items.slice import Slice
from crumb.bakery_items.crumb import Crumb
import crumb.settings as settings

cr = CrumbRepository()

class TestBasics(unittest.TestCase):
    def test_crumb(self):
        cr.reset()

        settings.multislicer = False
        @crumb(output=int, name='func_test')
        def func(aa=3):
            return aa
        self.assertIn('func_test', cr.crumbs)
        self.assertNotIn('func', cr.crumbs)
    
class TestSlice(unittest.TestCase):
    def test_slice(self):
        cr.reset()

        import tests.sample_crumbs # crumbs needed

        s = Slice(name='first slice')
        s.add_crumb('a1', cr.get_crumb('a1'))
        s.add_crumb('a2', cr.get_crumb('a2'))

        # print(s)
        # print(s.get_deps())
        # print(s.to_json())

        s2 = Slice(name='first slice')
        s2.from_json(s.to_json())
        print(s2.to_json())

        self.assertEqual(s.to_json(), s2.to_json())

class TestJSON(unittest.TestCase):
    def test_tofrom(self):
        cr.reset()

        import tests.singleton_m2 # crumbs needed!

        c_f2 = cr.get_crumb('f2')
        c_f2_new = Crumb.create_from_json(c_f2.to_json())
        self.assertEqualCrumbs(c_f2, c_f2_new)

        c_fpi = cr.get_crumb('fpi')
        c_fpi_new = Crumb.create_from_json(c_fpi.to_json())
        self.assertEqualCrumbs(c_fpi, c_fpi_new)

    def assertEqualCrumbs(self, a, b):
        self.assertEqual(a.name, b.name)
        self.assertEqual(a.input, b.input)
        self.assertEqual(a.output, b.output)
        self.assertEqual(a.file, b.file)
        self.assertEqual(a.func.__name__, b.func.__name__)
