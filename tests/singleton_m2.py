

from crumb import crumb, CrumbRepository

import numpy as np

@crumb(input={'hue': int}, output=int)
def f2(hue):
    return hue + 2
    
    
@crumb(input={'hue': int}, output=int, deps=np)
def fpi(hue):
    return np.pi + hue

