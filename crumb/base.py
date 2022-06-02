
import inspect

class Crumb:
    def __init__(self, name, input=None, output=None, deps=None, func=None, save_exec=True):
        self._crumb_check_input(func, input)

        self.name = name
        self.input = input
        self.output = output
        self.deps = deps
        self.func = func

        self.save_exec = save_exec
        self.last_exec = None
    
    def _get_args(self, func):
        sign = inspect.signature(func)
        return { k:v.default for k,v in sign.parameters.items()}

    def _crumb_check_input(self, func, input):
        # check if input parameter is a dictionary
        if input is not None and type(input) is not dict:
            raise ValueError('input parameter must be dict, obtained' + str(type(input)))
        
        # if there are inputs to be evaluated
        func_args = self._get_args(func)
        # check if all elements defined in input are in the function call:
        _not_valid = list()
        if 'kwargs' in func_args.keys():
            # for the functions that have more parameters we can not check if the list we have really exist
            pass
        elif input is not None:
            # first check for the ones that are not in the function
            for i in input.keys():
                if i not in func_args:
                    _not_valid.append(i)

        # then check for the ones that do not have a default parameter, and they must be in there
        _not_valid_missing = list()
        for i, t in func_args.items():
            if t is inspect.Parameter.empty:
                if input is None or i not in input:
                    _not_valid_missing.append(i)

        # compile the relation of errors
        err = ''
        if len(_not_valid) > 0:
            err += 'input definition for a parameter that is not in the function: "{}"'.format('", "'.join(_not_valid))
        if len(_not_valid_missing) > 0:
            if len(err) > 0:
                err += '\n\tAND\n'
            err += 'input definition missing for a parameter without default value: "{}"'.format('", "'.join(_not_valid_missing))
        if len(err) > 0:
            raise ValueError(err)

    def run(self, input):
        if self.save_exec:
            self.last_exec = self.func(**input)
            return self.last_exec
        else:
            return self.func(**input)

    def __repr__(self):
        return f'{self.__class__.__name__} at {hex(id(self))} with ({self.input})=>({str(self.output)})'

    def __str__(self):
        return self.__repr__()

class Slice:
    def __init__(self, name, save_exec=True):
        self.name = name
        self.input = dict() # name: type

        self.output = dict() # name: type
        self._output_mapping = dict() # name: node, name

        self.save_exec = save_exec
        
        self.crumbs = dict()

    def add_crumb(self, crumb):
        self.crumbs[crumb.name] = {'crumb': crumb,
                                   'is_linked': False}

    def get_deps(self):
        return set([i.deps for i in self.crumbs.values()])

    
