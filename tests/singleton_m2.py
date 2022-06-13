"""Test if CrumbRepository is a singleton pt2"""
import math
from crumb import crumb, CrumbRepository

cr = CrumbRepository()


@crumb(input={'hue': int}, output=int, name='f2')
def function_two(hue: int) -> int:
    """Return a number + 2"""
    return hue + 2


@crumb(input={'hue': int}, output=float, name='fpi')
def function_pi(hue: int) -> float:
    """Return a number + pi"""
    return math.pi + hue
