"""Basic tests"""
from crumb import crumb, CrumbRepository
from crumb.bakery_items.slice import Slice
from crumb.bakery_items.crumb import Crumb

cr = CrumbRepository()


def test_crumb() -> None:
    """Check if Crumb can be created"""
    cr.reset()

    @crumb(output=int, name='func_test')
    def func(a_input: int = 3) -> int:
        return a_input
    assert 'func_test' in cr.crumbs
    assert 'func' not in cr.crumbs


def test_slice() -> None:
    """Test if we can start a slice and if the json can be used"""
    import tests.sample_crumbs  # crumbs needed
    slice = Slice(name='first slice')
    slice.add_bakery_item('a1', cr.get_crumb('a1'))
    slice.add_bakery_item('a2', cr.get_crumb('a2'))
    # print(s)
    # print(s.get_deps())
    # print(s.to_json())
    slice_2 = Slice(name='first slice')
    slice_2.from_json(slice.to_json())
    # print(s2.to_json())
    assert slice.to_json() == slice_2.to_json()


def assert_equal_crumbs(crumb_a: Crumb, crumb_b: Crumb) -> None:
    """Check if two crumbs are equal"""
    assert crumb_a.name == crumb_b.name
    assert crumb_a.input == crumb_b.input
    assert crumb_a.output == crumb_b.output
    assert crumb_a.file == crumb_b.file
    assert crumb_a.func.__name__ == crumb_b.func.__name__


def test_crumb_tofrom_json() -> None:
    """Test if we can reload the Crumb from json and if it is equal"""
    import tests.singleton_m2  # crumbs needed!
    c_f2 = cr.get_crumb('f2')
    c_f2_new = Crumb.create_from_json(c_f2.to_json())
    assert_equal_crumbs(c_f2, c_f2_new)
    c_fpi = cr.get_crumb('fpi')
    c_fpi_new = Crumb.create_from_json(c_fpi.to_json())
    assert_equal_crumbs(c_fpi, c_fpi_new)


if __name__ == '__main__':
    test_crumb()
    test_slice()
    test_crumb_tofrom_json()
