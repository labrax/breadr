"""Test if the singleton is working"""


def test_singleton():
    import tests.singleton_m1 as s1
    m1c = s1.CrumbRepository()
    import tests.singleton_m2 as s2
    m2c = s2.CrumbRepository()
    assert m1c == m2c
