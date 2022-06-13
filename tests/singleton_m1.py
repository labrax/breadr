"""Test if CrumbRepository is a singleton pt1"""
from crumb import crumb, CrumbRepository

cr = CrumbRepository()


@crumb(input={'hue': int}, output=int)
def function_one(hue: int) -> int:
    "Return a number + 1"
    return hue + 1
