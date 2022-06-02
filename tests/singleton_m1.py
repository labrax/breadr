
from crumb import crumb, CrumbRepository

@crumb(input={'hue': int}, output=int)
def f1(hue):
    return hue + 1