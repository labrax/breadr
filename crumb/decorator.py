
import functools

from crumb.repository import CrumbRepository

# decorator to add breadr functionality to functions
def crumb(_func=None, *, output, input=None, deps=None, name=None):
    def decorator_add(func):
        c = CrumbRepository()
        CrumbRepository().add_crumb(name=name, 
                                    func=func, 
                                    deps=deps,
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
                                    deps=deps,
                                    input=input, 
                                    output=output)
        return decorator_add(_func)
