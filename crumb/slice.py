
import itertools
import os
import json

from .crumb import Crumb

class Slice:
    def __init__(self, name, save_exec=True):
        self.name = name
        self.input = dict() # name: type

        self.output = dict() # name: type
        self._output_mapping = dict() # name: node, name

        self.save_exec = save_exec
        self.last_exec = None
        
        self.crumbs = dict()

    def add_crumb(self, name, crumb):
        if name in self.crumbs:
            raise ValueError(f'crumb {name} already in Slice')
        self.crumbs[name] = {'crumb': crumb,
                             'is_linked': False}

    def get_deps(self):
        return set(itertools.chain(*[i['crumb'].deps for i in self.crumbs.values()]))

    def __repr__(self):
        return f'{self.__class__.__name__} at {hex(id(self))} with {len(self.crumbs)} crumbs'

    def __str__(self):
        return self.__repr__()    

    def to_json(self):
        this_structure = {
            'slice_name': self.name,
            'input': {i:j.__name__ for i,j in self.input.items()} if self.input else {},
            'output': {
                'objects': {i:j.__name__ for i,j in self.output.items()} if self.output else {},
                'mapping': {i:j.__name__ for i,j in self._output_mapping.items()} if self._output_mapping else {},
            },
            'crumbs': {i: {
                'crumb': j['crumb'].to_json(), 
                'is_linked': j['is_linked']
            } for i, j in self.crumbs.items()} if self.crumbs else {},
            'state': {
                'save_exec': self.save_exec,
                'last_exec': self.last_exec
            }
        }
        return json.dumps(this_structure)

    def from_json(self, json_str):
        json_str = json.loads(json_str)
        self.name = json_str['slice_name']
        
        self.input = {i:eval(j) for i,j in json_str['input'].items()} if json_str['input'] else {}
        self.output = {i:eval(j) for i,j in json_str['output']['objects'].items()} if json_str['output']['objects'] else {}
        self._output_mapping = {i:eval(j) for i,j in json_str['output']['mapping'].items()} if json_str['output']['mapping'] else {}

        self.crumbs = {i:{
            'crumb': Crumb.create_from_json(j['crumb']), 
            'is_linked': j['is_linked']
        } for i, j in json_str['crumbs'].items()} if json_str['crumbs'] else {}
        self.save_exec = json_str['state']['save_exec']
        self.last_exec = json_str['state']['last_exec']

    def save(self, path, overwrite=False):
        if not overwrite:
            if os.path.exists(path):
                raise FileExistsError(f'File {path} already exists. Use parameter "overwrite" to replace.')
        with open(path, 'w') as of:
            of.write(self.to_json)

    def load(self, path):
        with open(path) as f:
            self.from_json(f.read())
    