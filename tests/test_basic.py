"""Basic tests"""
import pytest
from crumb.settings import Settings
from crumb import crumb, CrumbRepository
from crumb.bakery_items.slice import Slice
from crumb.bakery_items.crumb import Crumb

cr = CrumbRepository()


def test_crumb() -> None:
    """Check if Crumb can be created"""
    cr.reset()
    Settings.LOGGING_WARNING_TWICE = True
    with pytest.warns(UserWarning):
        @crumb(output=int, name='func_test')
        def func(a_input: int = 3) -> int:
            return a_input
    assert 'func_test' in cr.crumbs
    assert 'func' not in cr.crumbs


def test_crumb_invalid() -> None:
    """Check if errors are popping in Crumb creation"""
    Settings.LOGGING_WARNING_TWICE = True
    # get all warnings about functions defined in here
    with pytest.warns(UserWarning):
        # check for input that is not well formated
        with pytest.raises(ValueError):
            @crumb(name='func_badly_formatted', input=int, output=int)
            def func_badly_formatted(a_input: int = 3) -> int:
                return a_input

        # check for wrong definition for input
        with pytest.raises(ValueError):
            @crumb(name='func_bad_definition', input={'a_input': 'int'}, output=int)  # instead of str 'int' it should have been int
            def func_bad_definition(a_input: int = 3) -> int:
                return a_input

        # file that does not exist
        with pytest.raises(FileNotFoundError):
            def dummy_function() -> None:
                pass
            invalid_crumb = Crumb('dummy', 'this_file_doesnt_exist.py', dummy_function)
            invalid_crumb.load_from_file(filepath='this_file_doesnt_exist.py', this_name='invalid')

        # check for file that exist but is invalid
        with pytest.raises(RuntimeError):
            def dummy_function() -> None:
                pass
            invalid_crumb = Crumb('dummy', 'README.md', dummy_function)
            invalid_crumb.load_from_file(filepath='README.md', this_name='invalid')

        # check for input that is not in the function
        with pytest.raises(ValueError):
            @crumb(name='func_missing_definition', input={'not_in_function': int}, output=int)
            def func_missing_definition(missing_in_definition: int) -> int:
                return missing_in_definition

        with pytest.warns(UserWarning):
            @crumb(input={'a_input': int}, output=int)
            def func_missing_name(a_input) -> int:
                return a_input


def test_slice_json_from_to() -> None:
    """Test if we can start a slice and if the json can be used"""
    # crumbs needed
    import tests.sample_crumbs  # pylint: disable=import-outside-toplevel
    assert tests.sample_crumbs.get5() == 5  # excuse to use import
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
    # crumbs needed!
    import tests.singleton_m2  # pylint: disable=import-outside-toplevel
    assert tests.singleton_m2.function_two(2) == 4  # excuse to use import and remove pep8 warning
    c_f2 = cr.get_crumb('f2')
    c_f2_new = Crumb.create_from_json(c_f2.to_json())
    assert_equal_crumbs(c_f2, c_f2_new)
    c_fpi = cr.get_crumb('fpi')
    c_fpi_new = Crumb.create_from_json(c_fpi.to_json())
    assert_equal_crumbs(c_fpi, c_fpi_new)


if __name__ == '__main__':
    test_crumb()
    test_slice_json_from_to()
    test_crumb_tofrom_json()
