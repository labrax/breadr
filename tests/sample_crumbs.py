"""Sample usage of @crumb decorator"""
from crumb import crumb


@crumb(output=int, name='a1')
def func(a_input: int = 1) -> int:
    """Return the input"""
    return a_input


@crumb(output=int, name='a2')
def func(a_input: int = 2) -> int:  # it is redefined, this is to check if @crumb works
    """Return the input"""
    return a_input


# these are used in test_graph
@crumb(output=int, name='get5')
def get5() -> int:
    """Return 5"""
    return 5


@crumb(input={'a': int}, output=int, name='add15')
def add15(a: int, b_input: int = 15) -> int:
    """Return a + b_input"""
    return a + b_input


@crumb(input={'a': int, 'b': int}, output=int, name='minus')
def minus(a: int, b: int) -> int:
    """Return a - b"""
    return a - b
