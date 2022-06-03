

from crumb import crumb, CrumbRepository

import math

@crumb(input={'hue': int}, output=int)
def f2(hue):
    return hue + 2
    
    
@crumb(input={'hue': int}, output=int, deps=math)
def fpi(hue):
    return np.pi + hue

