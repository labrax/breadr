
import inspect
import json
import importlib
import os


class Crumb:
    def __init__(self, name, file, func, input=None, output=None, deps=None, save_exec=True):
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
            },
            'state': {
                'save_exec': self.save_exec,
                'last_exec': self.last_exec
            }
        }
        return json.dumps(this_structure)

    def from_json(self, json_str):
        from crumb.repository import CrumbRepository
        cr = CrumbRepository()

        json_str = json.loads(json_str)

        crumbs_repo = dict()
        redirect_status = cr._redirect
        cr.redirect({'target': crumbs_repo})
        # load file to recover crumbs
        path, pkg = os.path.split(json_str['executable']['file'])
        spec = importlib.util.spec_from_file_location(os.path.splitext(pkg)[0], json_str['executable']['file'])
        mod = importlib.util.module_from_spec(spec)
        m = spec.loader.exec_module(mod)
        # get crumb
        restored_crumb = cr.get_crumb(json_str['name'])
        self.name = restored_crumb.name
        self.input = restored_crumb.input
        self.output = restored_crumb.output
        self.file = restored_crumb.file
        self.deps = restored_crumb.deps
        self.func = restored_crumb.func
        self.save_exec = restored_crumb.save_exec
        self.last_exec = restored_crumb.last_exec
        cr._redirect = redirect_status
        return

        self.name = json_str['name']
        self.input = {i:eval(j) for i,j in json_str['input'].items()} if json_str['input'] else {}
        self.output = eval(json_str['output'])

        self.file = json_str['executable']['file']

        mute_status = cr._mute
        cr.mute() # protection against overwriting definitions

        self.deps = {}
        for dn, ds in json_str['executable']['deps'].items():
            # first lets try to find the module
            spec = importlib.util.find_spec(dn)
            if spec is None:
                if ds['origin'] == 'built-in': # if it is built-in the installation is missing something
                    cr.unmute()
                    cr._mute = mute_status
                    raise ImportError(f'cannot find module {dn}')
                else: # lets try the file location
                    spec = importlib.util.spec_from_file_location(dn, ds['origin'])
            mod = importlib.util.module_from_spec(spec)
            m = spec.loader.exec_module(mod) # this could lead to overwriting modules; this is necessary to ensure that the modules are in a working state
            self.deps[mod] = ds['called_as']

        # print(json_str['executable']['file'])

        path, pkg = os.path.split(json_str['executable']['file'])
        spec = importlib.util.spec_from_file_location(os.path.splitext(pkg)[0], json_str['executable']['file'])
        mod = importlib.util.module_from_spec(spec)
        m = spec.loader.exec_module(mod)

        self.func = getattr(mod, json_str['executable']['func'])
        self.save_exec = json_str['state']['save_exec']
        self.last_exec = json_str['state']['last_exec']

        cr.unmute() # unmute after loading modules
        cr._mute = mute_status

    @classmethod
    def create_from_json(self, json_str):
        def f1(a=1):
            return None
        crumb = Crumb('f1', '.', f1, input=None, output=None, deps=None, save_exec=True)
        crumb.from_json(json_str)
        return crumb
