
import inspect
import warnings

from crumb.base import Crumb

class CrumbRepository(object):
    def __new__(cls):
        global crumb_repository_instance
        try: crumb_repository_instance
        except NameError:
            crumb_repository_instance = super(CrumbRepository, cls).__new__(cls)
            crumb_repository_instance.reset()
        return crumb_repository_instance

    def add_crumb(self, name, func, deps, input, output):
        if name is None:
            name = inspect.getfile(inspect.currentframe().f_back.f_back) + ':' + func.__name__
            if not self._warned_names:
                warnings.warn('Functions without explicit names will be given names from their filepath and name. Give a name to the crumb using the "name" parameter.', UserWarning)
                self._warned_names = True
        if name in self.crumbs:
            raise ValueError(f'name "{name}" already used in the repository')
        self.crumbs[name] = Crumb(name=name, input=input, output=output, func=func, deps=deps, file=inspect.getfile(inspect.currentframe().f_back.f_back))
        #from pprint import pprint
        #print(name)
        #pprint(self.crumbs[name])

    def get_crumb(self, name):
        return self.crumbs[name]

    def reset(self):
        self.crumbs = dict()
        self._warned_names = False