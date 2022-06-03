
import itertools
import os
import json

from .crumb import Crumb
from . import __slicer_version__

from .node import Node

class Slice:
    def __init__(self, name, save_exec=True):
        self.version = __slicer_version__
        self.name = name
        self.input = dict() # {'name': <type>}
        self._input_mapping = dict() # {'input_name': {'node name': ['Node input name']}}
        self.output = dict() # {'name': <type>}
        self._output_mapping = dict() # {'output_name': {'node name': ['Node output name']}}

        self.save_exec = save_exec
        self.last_exec = {}
        
        self.crumbs = dict() # {'name given': {'crumb': crumb, 'is_used': bool}}
        self.nodes = dict() # {'identifier': Node}

        self.is_used = False # if it is being used in a Node

    def add_crumb(self, name, crumb):
        if name in self.crumbs:
            raise ValueError(f'crumb "{name}" already in Slice')
        self.crumbs[name] = {'crumb': crumb,
                             'is_used': False}

    def add_node(self, crumb_name):
        n = Node(self.crumbs[crumb_name]['crumb'])
        self.nodes[n.name] = n
        return n.name

    def remove_node(self, node_name):
        for i in self._input_mapping.values():
            if node_name in i:
                raise RuntimeError(f'cannot remove "{node_name}" as it is linked to input')

        for i in self._output_mapping.values():
            if node_name in i:
                raise RuntimeError(f'cannot remove "{node_name}" as it is linked to output')

        if self.nodes[node_name].has_links():
            raise RuntimeError(f'cannot remove "{node_name}" as it is connect in the graph')
        
        self.nodes.pop(node_name)

    def _check_input_exists(self, name, check_mapping=True):
        if name not in self.input:
            raise RuntimeError(f'"{name}" not in input list')
        if check_mapping:
            if self._input_mapping[name]:
                raise RuntimeError(f'"{name}" contains mapping to input')

    def _check_output_exists(self, name, check_mapping=True):
        if name not in self.output:
            raise RuntimeError(f'"{name}" not in output list')
        if check_mapping:
            if self._output_mapping[name]:
                raise RuntimeError(f'"{name}" contains mapping to output')

    def _check_node_exists(self, node_name, node_input=None, node_output=None):
        """
        Check if Node and (optional) parameters exist
        @param node_name: name of the node
        @param node_input: input in node
        @param node_output: output in node
        """
        if node_name not in self.nodes:
            raise RuntimeError(f'"{node_name}" not in slice')
        if node_input is not None:
            if node_input not in self.nodes[node_name].input.keys():
                raise RuntimeError(f'"{node_input}" not in "{node_name}" input list')
        if node_output is not None:
            if node_output not in self.nodes[node_name].output.keys():
                raise RuntimeError(f'"{node_output}" not in "{node_name}" output list')

    # slice input and output functions
    def add_input(self, name, type):
        """
        Add input to Slice
        @param name: name
        @param type: object type
        """
        if name in self.input:
            raise RuntimeError(f'"{name}" already in input list')
        self.input[name] = type
        self._input_mapping[name] = {}

    def remove_input(self, name):
        """
        Remove Slice input
        @param name: name
        """
        self._check_input_exists(name, check_mapping=True) # if doesn't exist or in mapping not good to remove
        self.input.pop(name)
        self._input_mapping.pop(name)

    def add_output(self, name, type):
        """
        Add output to Slice
        @param name: name
        @param type: object type
        """
        if name in self.output:
            raise RuntimeError(f'"{name}" already in output list')
        self.output[name] = type
        self._output_mapping[name] = {}

    def remove_output(self, name):
        """
        Remove Slice output
        @param name: name
        """
        self._check_output_exists(name, check_mapping=True) # if doesn't exist or in mapping not good to remove
        self.output.pop(name)
        self._output_mapping.pop(name)

    # mapping functions
    def add_input_mapping(self, name, node_name, node_input):
        """
        Add a mapping between a Node (defined within the node) and the Slice input
        @param name: name of the input
        @param node_name: name of the node
        @param node_input: name of the node input
        """
        self._check_input_exists(name, check_mapping=False)
        self._check_node_exists(node_name, node_input)
        if self.input[name] != self.nodes[node_name].get_input_type(node_input):
            raise RuntimeError(f'"{name}" has got different type than input for node "{node_name}" (input: {node_input}). types are: "{self.input[name]}" and "{self.nodes[node_name].input[node_input]}"')
        if not name in self._input_mapping:
            self._input_mapping = dict()
        if not node_name in self._input_mapping[name]:
            self._input_mapping[name][node_name] = list()
        self._input_mapping[name][node_name].append(node_input)

    def remove_input_mapping(self, name, node_name, node_input):
        """
        Remove mapping between Node and Slice input
        @param name: name of the input
        @param node_name: name of the node
        @param node_input: name of the node input
        """
        self._check_input_exists(name, check_mapping=False)
        if not node_name in self._input_mapping[name]:
            raise RuntimeError(f'"{node_name} not in input mapping')
        self._input_mapping[name][node_name].pop(node_input)
        if len(self._input_mapping[name][node_name]) == 0:
            self._input_mapping[name].pop(node_name)
        if len(self._input_mapping[name]) == 0:
            self._input_mapping.pop(name)

    def add_output_mapping(self, name, node_name, node_output):
        """
        Add a mapping between a Node (defined within the node) and the Slice output
        @param name: the name of the output
        @param node_name: the name of the node
        @param node_output: the name of the node output
        """
        self._check_output_exists(name, check_mapping=False)
        self._check_node_exists(node_name, node_output)
        if self.output[name] != self.nodes[node_name].get_output_type(node_output):
            raise RuntimeError(f'"{name}" has got different type than output for node "{node_name}" (output {node_output}). types are: "{self.output[name]}" and "{self.nodes[node_name].output[node_output]}"')
        if not name in self._output_mapping:
            self._output_mapping = dict()
        if not node_name in self._output_mapping[name]:
            self._output_mapping[name][node_name] = list()
        self._output_mapping[name][node_name].append(node_output)

    def remove_output_mapping(self, name, node_name, node_output):
        """
        Remove mapping between Node and Slice output
        @param name: name of the output
        @param node_name: name of the node
        @param node_output: name of the node output
        """
        self._check_output_exists(name, check_mapping=False)
        if not node_name in self._output_mapping[name]:
            raise RuntimeError(f'"{node_name} not in output mapping')
        self._output_mapping[name][node_name].pop(node_output)
        if len(self._output_mapping[name][node_name]) == 0:
            self._output_mapping[name].pop(node_name)
        if len(self._output_mapping[name]) == 0:
            self._output_mapping.pop(name)
    #

    def add_link(self, nodeA, nodeA_output, nodeB, nodeB_input):
        """
        Links two nodes
        @param nodeA: first node
        @param nodeA_output: first node output name
        @param nodeB: second node
        @param nodeB_output: second node output name
        """
        self._check_node_exists(nodeA, node_output=nodeA_output)
        self._check_node_exists(nodeB, node_input=nodeB_input)
        A = self.nodes[nodeA]
        B = self.nodes[nodeB]
        A.add_output(this_output_name=nodeA_output, other_node=B, other_node_variable=nodeB_input)
        B.add_input(this_variable=nodeB_input, other_node=A, other_node_name=nodeA_output)

    def get_deps(self):
        return set(itertools.chain(*[i['crumb'].deps for i in self.crumbs.values()]))

    def __repr__(self):
        return f'{self.__class__.__name__} at {hex(id(self))} with {len(self.crumbs)} crumbs'

    def __str__(self):
        return self.__repr__()    

    def to_json(self):
        this_structure = {
            'slice_name': self.name,
            'version': __slicer_version__,
            'input': {
                'objects': {i:j.__name__ for i,j in self.input.items()} if self.input else {},
                'mapping': self._input_mapping
            },
            'output': {
                'objects': {i:j.__name__ for i,j in self.output.items()} if self.output else {},
                'mapping': self._output_mapping
            },
            'crumbs': {i: {
                'crumb': j['crumb'].to_json(), 
                'is_used': j['is_used']
            } for i, j in self.crumbs.items()} if self.crumbs else {},
            'state': {
                'save_exec': self.save_exec,
                'last_exec': self.last_exec
            }
        }
        return json.dumps(this_structure)

    def from_json(self, json_str):
        json_str = json.loads(json_str)
        if json_str['version'] > __slicer_version__:
            raise ImportError('imported file has a higher version')
        self.version = __slicer_version__
        self.name = json_str['slice_name']
        
        self.input = {i:eval(j) for i,j in json_str['input']['objects'].items()} if json_str['input']['objects'] else {}
        self._input_mapping = json_str['input']['mapping']
        self.output = {i:eval(j) for i,j in json_str['output']['objects'].items()} if json_str['output']['objects'] else {}
        self._output_mapping = json_str['output']['mapping']

        self.crumbs = {i:{
            'crumb': Crumb.create_from_json(j['crumb']), 
            'is_used': j['is_used']
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
    