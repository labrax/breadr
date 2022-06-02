
import unittest

class TestCrumbRepositorySingleton(unittest.TestCase):
    def test_singleton(self):
        import tests.singleton_m1 as s1
        m1c = s1.CrumbRepository()
        import tests.singleton_m2 as s2
        m2c = s2.CrumbRepository()

        self.assertEqual(m1c, m1c)