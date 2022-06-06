
import functools
import inspect

import crumb.settings as settings
from crumb.repository import CrumbRepository

import warnings

# decorator to add breadr functionality to functions
def crumb(_func=None, *, output, input=None, name=None):
    """
    Decorator that adds crumb reference to a function
    @param _func: the function under the decorator
    @param output: the output of the function, int, float, class, ..., obtained from type()
    @param input: the input of the function: {'param1': int, 'param2': class, ...}
    @param name: short name for this function
    """
    # check if the decorator is inside a function/class or on top level of file. this is needed to be able to reload
    context = inspect.getframeinfo(inspect.currentframe().f_back, context=1)
    context_filename = context.filename
    context_function = context.function
    if settings.multislicer:
        if context_function != '<module>':
            raise RuntimeError(f'When using multislicer, @crumb decorator must be used in a file top level (not inside "{context_function}")')
        if context_filename == '<stdin>':
            raise RuntimeError(f'When using multislicer, @crumb decorator must be used in a file top level ("<stdin>" will not work)')
    elif context_function != '<module>' or context_filename == '<stdin>':
        warnings.warn('Since function is not in a module root it might not be possible to reload it after saving')

    def decorator_add(func):
        c = CrumbRepository()
        CrumbRepository().add_crumb(name=name, 
                                    func=func,
                                    input=input, 
                                    output=output)
    
        @functools.wraps(func)
        def wrapper_function(*args, **kwargs):
            # safeguard the function, more functionality can be added here later, e.g. error checking
            value = func(*args, **kwargs)
            return value
        return wrapper_function

    if _func is None: # decorator called with arguments
        return decorator_add
    else: # decorator called without arguments
        c = CrumbRepository()
        CrumbRepository().add_crumb(name=name, 
                                    func=_func,
                                    input=input, 
                                    output=output)
        return decorator_add(_func)
