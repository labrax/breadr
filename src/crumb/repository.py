"""
Module repository
This module stores the definition of CrumbRepository

Note, pylint comments are due to variables being defined inside reset() rather than __init__() due to singleton
"""
from typing import Callable, Optional, Dict
import inspect
import warnings

from crumb.bakery_items.crumb import Crumb


class CrumbRepository:
    """
    CrumbRepository stores the different crumbs identified through decorators
    """
    CRUMB_REPOSITORY_INSTANCE = None

    def __new__(cls):
        if CrumbRepository.CRUMB_REPOSITORY_INSTANCE is None:
            CrumbRepository.CRUMB_REPOSITORY_INSTANCE = super().__new__(cls)
            CrumbRepository.CRUMB_REPOSITORY_INSTANCE.reset()
        return CrumbRepository.CRUMB_REPOSITORY_INSTANCE

    def add_crumb(self, name: str, func: Callable, input: Optional[Dict[str, type]], output: Optional[type]):
        """
        Adds a crumb to the repository. Do not call this function directly, use the decorator.
        @param name: short name for this function, if None name will be given from the filepath
        @param func: the function
        @param input: the input of the function: {'param1': int, 'param2': class, ...}
        @param output: the output of the function, int, float, class, ..., obtained from type()
        """
        if self._mute:
            return
        # if no name is given get one from file name
        if name is None:
            name = inspect.getfile(inspect.currentframe().f_back.f_back) + ':' + func.__name__
            if not self._warned_names:
                warnings.warn('Functions without explicit names will be given names from their filepath and name." \
                              + " Give a name to the crumb using the "name" parameter.', UserWarning)
                self._warned_names = True  # pylint: disable=attribute-defined-outside-init
        # check existance in repo
        if (self._redirect is not None and name in self._redirect) or (self._redirect is None and name in self.crumbs):
            raise ValueError(f'name "{name}" already used in the repository')
        # process types
        if output.__class__.__name__ != 'type':
            raise ValueError(f'"{output}" is not a type. maybe you wanted to do type("{output}")?')
        # check input
        if input:
            if not isinstance(input, dict):
                raise ValueError(f'Input must be a dict or nothing, not "{type(input)}".')
            _invalid_input = []
            for i, j in input.items():
                if j.__class__.__name__ != 'type':
                    _invalid_input.append(i)
            if len(_invalid_input) > 0:
                _invalid_input_str = '", "'.join(_invalid_input)
                raise ValueError(f'At least one input parameter is not a type. check: "{_invalid_input_str}"')
        # starts the new crumb
        # it is expected that there is always at least 2 frames up: this one, the decorator call, and the module.
        new_crumb = Crumb(name=name, input=input, output=output, func=func, file=inspect.getfile(inspect.currentframe().f_back.f_back))  # type: ignore
        if self._redirect:
            self._redirect[name] = new_crumb
        else:
            self.crumbs[name] = new_crumb
        # from pprint import pprint
        # print(name)
        # pprint(self.crumbs[name])

    def get_crumb(self, name: str):
        """
        Return the crumb object for a given name
        @param name
        """
        if self._redirect:
            return self._redirect[name]
        return self.crumbs[name]

    def reset(self):
        """
        Clear the stored data
        """
        self.crumbs = {}  # pylint: disable=attribute-defined-outside-init
        self._warned_names = False  # pylint: disable=attribute-defined-outside-init
        self._mute = False  # pylint: disable=attribute-defined-outside-init
        self._redirect = None  # pylint: disable=attribute-defined-outside-init

    def get_redirected(self):
        """
        Obtian the current redirect setting
        """
        return self._redirect

    def redirect(self, new_redirection: dict):
        """
        Use this to redirect creation of crumbs to another dictionary
        To pass the object as reference it needs to be inside a dictionary with the key target, e.g. use the parameter to with {'target': dict()}
        @param new_redirection: the object with the data
        """
        self._redirect = new_redirection['target']  # pylint: disable=attribute-defined-outside-init

    def mute(self):
        """
        Stops collecting crumbs
        """
        self._mute = True  # pylint: disable=attribute-defined-outside-init

    def unmute(self):
        """
        Restarts collecting crumbs
        """
        self._mute = False  # pylint: disable=attribute-defined-outside-init
