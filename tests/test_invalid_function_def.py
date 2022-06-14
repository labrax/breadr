"""Test invalid functions"""
import pytest
import crumb
import crumb.settings

crumb.settings.USE_MULTISLICER = False


def test_definition_missing_input() -> None:
    """Test if we are missing input without default value @crumb decorator"""
    crumb.settings.multislicer = False
    with pytest.warns(UserWarning):
        with pytest.raises(ValueError):
            @crumb.crumb(output=int)
            def func(valid):
                return valid


def test_definition_but_not_in_params() -> None:
    """Test if we are setting invalid input @crumb decorator"""
    crumb.settings.multislicer = False
    with pytest.warns(UserWarning):
        with pytest.raises(ValueError):
            @crumb.crumb(input='invalid', output=None)
            def func(valid):
                return valid


def test_definition_but_no_params() -> None:
    """Test if we are setting invalid parameters @crumb decorator"""
    crumb.settings.multislicer = False
    with pytest.warns(UserWarning):
        with pytest.raises(ValueError):
            @crumb.crumb(input='invalid', output=None)
            def func():
                return None


def test_definition_missing() -> None:
    """Test if we are missing the type for @crumb decorator output"""
    crumb.settings.multislicer = False
    with pytest.warns(UserWarning):
        with pytest.raises(ValueError):
            @crumb.crumb(output=None)
            def func(valid):
                return valid


def test_definition_missing_output() -> None:
    """Test if we are missing output in @crumb decorator"""
    crumb.settings.multislicer = False
    with pytest.raises(TypeError):
        # we want this error to trigger
        @crumb.crumb()  # pylint: disable=missing-kwoa
        def func(valid):
            return valid


if __name__ == '__main__':
    test_definition_but_no_params()
    test_definition_but_not_in_params()
    test_definition_missing()
    test_definition_missing_input()
    test_definition_missing_output()
