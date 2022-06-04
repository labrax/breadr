
import inspect
import json
import importlib
import os


class Crumb:
    def __init__(self, name, file, func, input=None, output=None, deps=None):
        """
        Starts a crumb object. Do not call this function directly, use the decorator.
        @param name: short name for this function
        @param file: filepath where the function comes from
        @param func: a function
        @param deps: dependencies in the format {module: ['module name', 'module name 2', ...], module2: ['module 2 name'], ...}
        @param input: the input of the function: {'param1': int, 'param2': class, ...}
        @param output: the output of the function, int, float, class, ..., obtained from type()
        @param save_exec: boolean save the output of the execution on memory?
        """
        self._crumb_check_input(func, input)

        self.name = name
        self.file = file.replace('\\', '/')
        self.input = input
        self.output = output
        self.deps = deps
        self.func = func

        self.is_used = False # if it is being used in a Node
    
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
        if self.func is None:
            self.reload()
        return self.func(**input)

    def __repr__(self):
        return f'{self.__class__.__name__} at {hex(id(self))} with ({self.input})=>({str(self.output)})'

    def __str__(self):
        return self.__repr__()

    def to_json(self):
        this_structure = {
            'name': self.name,
            'input': {i:j.__name__ for i,j in self.input.items()} if self.input else {},
            'output': self.output.__name__,
            'executable': {
                'file': self.file,
                'func': self.func.__name__,
                'deps': {i.__name__: {
                    'origin': i.__spec__.origin.replace('\\', '/'),
                    'called_as': j
                 } for i, j in self.deps.items() if i is not None}
            }
        }
        return json.dumps(this_structure)

    def from_json(self, json_str):
        json_str = json.loads(json_str)

        filepath = json_str['executable']['file']
        crumb_name = json_str['name']

        self.load_from_file(filepath, crumb_name)

    def load_from_file(self, filepath, crumb_name):
        from crumb.repository import CrumbRepository
        cr = CrumbRepository()
        # redirect crumbs creation to ensure we have the right function
        crumbs_repo = dict()
        redirect_status = cr._redirect
        cr.redirect({'target': crumbs_repo})
        # load file to recover crumbs
        path, pkg = os.path.split(filepath)
        spec = importlib.util.spec_from_file_location(os.path.splitext(pkg)[0], filepath)
        mod = importlib.util.module_from_spec(spec)
        m = spec.loader.exec_module(mod)
        # get crumb
        restored_crumb = cr.get_crumb(crumb_name)
        self.name = crumb_name
        self.input = restored_crumb.input
        self.output = restored_crumb.output
        self.file = filepath
        self.deps = restored_crumb.deps
        self.func = restored_crumb.func
        # restore redirection
        cr._redirect = redirect_status

    def reload(self):
        self.load_from_file(self.file, self.name)

    def prepare_for_exec(self):
        self.func = None

    @classmethod
    def create_from_json(self, json_str):
        def f1(a=1):
            return None
        crumb = Crumb('f1', '.', f1, input=None, output=None, deps=None)
        crumb.from_json(json_str)
        return crumb
