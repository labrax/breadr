

from crumb import crumb, CrumbRepository

import math

@crumb(input={'hue': int}, output=int, name='f2')
def f2(hue):
    return hue + 2
    
    
@crumb(input={'hue': int}, output=int, deps=math, name='fpi')
def fpi(hue):
    return math.pi + hue

