"""Definition for module Crumb"""
from __future__ import annotations
from typing import Optional, Dict, Callable, Any
import inspect
import json
from importlib.util import spec_from_file_location, module_from_spec
import os

from crumb.bakery_items.generic import BakeryItem
from crumb.logger import LoggerQueue, log, logging


class Crumb(BakeryItem):
    """
    Crumb is a class that contains information about how to run a function.
    @param name: name given to the crumb
    @param file: the file where this crumb was identified
    @param func: the underlying function
    @param input: the input of the function: {'param1': int, 'param2': class, ...}
    @param output: the output of the function, int, float, class, ..., obtained from type()
    """
    def __init__(self, name: str, file: str, func: Callable, input: Optional[Dict[str, type]] = None, output: Optional[type] = None):
        log(LoggerQueue.get_logger(), f'Starting crumb {name} from {file}', logging.DEBUG)
        self._crumb_check_input(func, input)
        super().__init__(name, input, output)
        self.file = file.replace('\\', '/')
        self.func = func

    def __repr__(self):
        return f'{self.__class__.__name__} at {hex(id(self))} with ({self.input})=>({str(self.output)})'

    def __str__(self):
        return self.__repr__()

    @classmethod
    def create_from_json(cls, json_str: str) -> Crumb:
        """
        Starts a Crumb based on a json string
        @param json_str
        """
        def dummy_function():
            return None
        crumb = Crumb('dummy_function', '.', dummy_function, input=None, output=None)
        crumb.from_json(json_str)
        return crumb

    def load_from_file(self, filepath: str, this_name: str) -> None:
        # in here to avoid recursive imports
        from crumb.repository import CrumbRepository
        crumb_repository = CrumbRepository()
        # redirect crumbs creation to ensure we have the right function
        crumbs_repo: dict = {}
        redirect_status = crumb_repository.get_redirected()
        crumb_repository.redirect({'target': crumbs_repo})
        # load file to recover crumbs
        _, pkg = os.path.split(filepath)
        spec = spec_from_file_location(os.path.splitext(pkg)[0], filepath)
        if spec is None:
            raise RuntimeError('Cannot load file "{filepath}" with function.')
        mod = module_from_spec(spec)
        _ = spec.loader.exec_module(mod)  # type: ignore  # already handled above
        # get crumb
        restored_crumb = crumb_repository.get_crumb(this_name)
        self.name = this_name
        self.input = restored_crumb.input
        self.output = restored_crumb.output
        self.file = filepath
        self.func = restored_crumb.func
        # restore redirection
        crumb_repository.redirect({'target': redirect_status})

    def from_json(self, json_str: str) -> None:
        json_obj = json.loads(json_str)
        filepath = json_obj['executable_file']
        crumb_name = json_obj['name']
        self.load_from_file(filepath, crumb_name)

    def to_json(self) -> str:
        this_structure = {
            'name': self.name,
            'executable_file': self.file
        }
        return json.dumps(this_structure)

    def reload(self) -> None:
        self.load_from_file(self.file, self.name)

    def run(self, input) -> Any:
        if self.func is None:
            self.reload()
        return self.func(**input)

    def _get_args(self, func: Callable) -> Dict[str, type]:
        sign = inspect.signature(func)
        return {k: v.default for k, v in sign.parameters.items()}

    def _crumb_check_input(self, func: Callable, input: Optional[Dict[str, type]]) -> None:
        # check if input parameter is a dictionary
        if input is not None and not isinstance(input, dict):
            raise ValueError('input parameter must be dict, obtained' + str(type(input)))
        # if there are inputs to be evaluated
        func_args = self._get_args(func)
        # check if all elements defined in input are in the function call:
        _not_valid = []
        if 'kwargs' in func_args.keys():
            # for the functions that have more parameters we can not check if the list we have really exist
            pass
        elif input is not None:
            # first check for the ones that are not in the function
            for i in input.keys():
                if i not in func_args:
                    _not_valid.append(i)
        # then check for the ones that do not have a default parameter, and they must be in there
        _not_valid_missing = []
        for i, in_type in func_args.items():
            if in_type is inspect.Parameter.empty:
                if input is None or i not in input:
                    _not_valid_missing.append(i)
        # compile the relation of errors
        err = ''
        if len(_not_valid) > 0:
            invalid_list = '", "'.join(_not_valid)
            err += f'input definition for a parameter that is not in the function: "{invalid_list}"'
        if len(_not_valid_missing) > 0:
            if len(err) > 0:
                err += '\n\tAND\n'
            invalid_missing = '", "'.join(_not_valid_missing)
            err += f'input definition missing for a parameter without default value: "{invalid_missing}"'
        if len(err) > 0:
            raise ValueError(err)
