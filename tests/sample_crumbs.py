
from crumb import crumb
import math
import os

@crumb(output=int, name='a1', deps=[math])
def func(aa=1):
    return aa

@crumb(output=int, name='a2', deps=os)
def func(aa=2):
    return aa

# these are used in test_graph
@crumb(output=int, name='get5')
def get5():
    return 5

@crumb(input={'a': int}, output=int, name='add15')
def add15(a, b=15):
    return a + b

@crumb(input={'a': int, 'b': int}, output=int, name='minus')
def minus(a, b):
    return a - b
#!