
from crumb import crumb
import math
import os

@crumb(output=int, name='a1', deps=[math])
def func(aa=1):
    return aa

@crumb(output=int, name='a2', deps=os)
def func(aa=2):
    return aa
