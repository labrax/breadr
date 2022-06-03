
import inspect
import warnings

from crumb.crumb import Crumb

class CrumbRepository(object):
    def __new__(cls):
        global crumb_repository_instance
        try: crumb_repository_instance
        except NameError:
            crumb_repository_instance = super(CrumbRepository, cls).__new__(cls)
            crumb_repository_instance.reset()
        return crumb_repository_instance

    def _check_deps(self, deps):
        if deps is not None:
            _not_module = list()
            for i in deps:
                if not inspect.ismodule(i):
                    _not_module.append(i)
            if len(_not_module) > 0:
                raise ValueError('dependencies added must be python modules. invalid dependencies are "{}"'.format('", "'.join(_not_module)))

    def add_crumb(self, name, func, deps, input, output):
        """
        Adds a crumb to the repository. Do not call this function directly, use the decorator.
        @param name: short name for this function, if None name will be given from the filepath
        @param func: the function
        @param deps: list of modules as used by the funciton [os, np] dependencies in the format {module: ['module name', 'module name 2', ...], module2: ['module 2 name'], ...}
        @param input: the input of the function: {'param1': int, 'param2': class, ...}
        @param output: the output of the function, int, float, class, ..., obtained from type()
        """
        if self._mute:
            return

        if name is None:
            name = inspect.getfile(inspect.currentframe().f_back.f_back) + ':' + func.__name__
            if not self._warned_names:
                warnings.warn('Functions without explicit names will be given names from their filepath and name. Give a name to the crumb using the "name" parameter.', UserWarning)
                self._warned_names = True
        if (self._redirect is not None and name in self._redirect) or (self._redirect is None and name in self.crumbs):
            raise ValueError(f'name "{name}" already used in the repository')
        
        # process dependencies
        if deps is not None and type(deps) is not list:
            deps = [deps]
        elif deps is None:
            deps = []
        self._check_deps(deps)
        deps = {i: [j for j, k in inspect.currentframe().f_back.f_back.f_locals.items() if k == i] for i in deps}

        new_crumb = Crumb(name=name, input=input, output=output, func=func, deps=deps, file=inspect.getfile(inspect.currentframe().f_back.f_back))
        if self._redirect:
            self._redirect[name] = new_crumb
        self.crumbs[name] = new_crumb
        #from pprint import pprint
        #print(name)
        #pprint(self.crumbs[name])

    def get_crumb(self, name):
        if self._redirect:
            return self._redirect[name]
        return self.crumbs[name]

    def reset(self):
        self.crumbs = dict()
        self._warned_names = False
        self._mute = False
        self._redirect = None

    def redirect(self, to):
        """
        Use this to redirect creation of crumbs to another dictionary
        To pass the object as reference it needs to be inside a dictionary with the key target, e.g. use the parameter to with {'target': dict()}
        """
        self._redirect = to['target']

    def mute(self):
        """
        Stops collecting crumbs
        """
        self._mute = True

    def unmute(self):
        """
        Restarts collecting crumbs
        """
        self._mute = False