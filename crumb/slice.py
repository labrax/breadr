
import itertools
import os
import json
import ast

import crumb.settings
from crumb.crumb import Crumb
from . import __slicer_version__

from crumb.node import Node
from crumb.slicers.slicers import get_slicer

class Slice:
    def __init__(self, name):
        self.version = __slicer_version__
        self.name = name
        self.input = dict() # {'name': <type>}
        self._input_mapping = dict() # {'input_name': {'node name': ['Node input name']}} # an input to slice can go to multiple bakery_items
        self.output = dict() # {'name': <type>}
        self._output_mapping = dict() # {'output_name': ('node name', 'Node output name'])} # an output can com from a single bakery_item
        
        self.crumbs = dict() # {'name given': {'crumb': crumb}}
        self.nodes = dict() # {'identifier': {'node': Node, 'type': 'slice crumb's name'}}

        self._graph_checked = False
        # these are the nodes that require input, if _graph_checked is True, they are in _input_mapping format is {node: {'node var': 'node var type'}}
        self._required_input = None
        self.last_execution_seq = None

        self.is_used = False # if it is being used in a Node

    def add_crumb(self, name, crumb):
        if name in self.crumbs:
            raise ValueError(f'crumb "{name}" already in Slice')
        self.crumbs[name] = {'crumb': crumb}

    def add_node(self, crumb_name):
        n = Node(self.crumbs[crumb_name]['crumb'])
        self.nodes[n.name] = {'node': n,
                              'type': crumb_name}
        return n.name

    def remove_node(self, node_name):
        for i in self._input_mapping.values():
            if node_name in i:
                raise RuntimeError(f'cannot remove "{node_name}" as it is linked to input')

        for i in self._output_mapping.values():
            if not i is None:
                if node_name in i:
                    raise RuntimeError(f'cannot remove "{node_name}" as it is linked to output')

        if self.nodes[node_name]['node'].has_links():
            raise RuntimeError(f'cannot remove "{node_name}" as it is connect in the graph')
        
        self.nodes.pop(node_name)

    def _check_input_exists(self, name, check_mapping=True):
        """
        Check if the name is in the list of input and (optional) if the mapping is defined
        @param name: name of input
        @param check_mapping: bool
        """
        if name not in self.input:
            raise RuntimeError(f'"{name}" not in input list')
        if check_mapping:
            if self._input_mapping[name]:
                raise RuntimeError(f'"{name}" contains mapping to input')

    def _check_output_exists(self, name, check_mapping=True):
        """
        Check if the name is in the list of output and (optional) if the mapping is defined
        @param name: name of output
        @param check_mapping: bool
        """
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
            if node_input not in self.nodes[node_name]['node'].input.keys():
                raise RuntimeError(f'"{node_input}" not in "{node_name}" input list')
        if node_output is not None:
            if node_output not in self.nodes[node_name]['node'].output.keys():
                raise RuntimeError(f'"{node_output}" not in "{node_name}" output list')

    def _check_graph_circular(self):
        if len(self.nodes) == 0:
            return

        visited = {}
        max_it = 0
        for it, stack_start in enumerate(self.nodes.keys()):
            if stack_start in visited:
                continue
            
            stack = [stack_start]
            while len(stack) > 0:
                current = stack.pop(0)
                for el in self.nodes[current]['node'].output.values(): # for each {'output name': {node, ['input name', ...]}}
                    for out_node, _ in el.items(): # for each {node, [...]}
                        if (out_node.name in visited) and (visited[out_node.name] == it):
                            raise RuntimeError(f'"{out_node.name}" already explored, graph is circular')
                        elif out_node.name not in visited:
                            stack.append(out_node.name)
                            visited[out_node.name] = it
            max_it = it
        return max_it

    def get_nodes_missing_input(self, only_in_output=True):
        if only_in_output:
            stack = list({self.nodes[node]['node'] for node, _ in self._output_mapping.values()})
        else:
            stack = self.nodes

        input_undefined = dict() # format is {node: {'node var': 'node var type'}}
        visited = set(stack)
        while len(stack) > 0:
            current = stack.pop(0)
            for inp, data in current.input.items():
                if data is None:
                    if current not in input_undefined:
                        input_undefined[current] = dict()
                    input_undefined[current][inp] = current.bakery_item.input[inp]
                else:
                    other_node = data[0]
                    visited.add(other_node)
                    stack.append(other_node)

        # these are the inputs missing within the graph
        return input_undefined

    def _check_input_complete(self, only_in_output=True):
        input_undefined = self.get_nodes_missing_input(only_in_output=only_in_output)
        self._required_input = input_undefined
        
        # remove the ones that will be given on the run call
        for _, data in self._input_mapping.items():
            for node_name, vars in data.items():
                node = self.nodes[node_name]['node']
                if node in input_undefined:
                    for i in vars:
                        input_undefined[node].pop(i)
                        if len(input_undefined[node]) == 0:
                            input_undefined.pop(node)

        # if we still have things missing we need to call quits as they need to be mapped
        if input_undefined:
            err = '\n'.join(['\t{}, elements: "{}"'.format(node, '", "'.join([str(i[0]) for i in inps])) for node, inps in input_undefined.items()])
            raise RuntimeError('input is undefined for at least one node:\n"{}"'.format(err))

    def _check_graph(self):
        self._check_graph_circular()
        self._check_input_complete()
        self._graph_checked = True

    def reload(self):
        for i in self.crumbs.values():
            i['crumb'].reload()

    def prepare_for_exec(self):
        for i in self.crumbs.values():
            i['crumb'].prepare_for_exec()

    def _compute_execution_seq(self):
        if not self._graph_checked:
            self._check_graph() # in case of error an exception will be raised

        nodes_seq = [] # format is: [{'node': node_id, 'deps': [node_id_1, node_id_2, ...]}]
        # start from slice input
        for node in self.nodes.values():
            this = {'node': node['node'], 'deps': []}
            for _, data in node['node'].input.items():
                if not data is None: # if none comes from slice!
                    this['deps'].append(data[0].name)
            nodes_seq.append(this)

        if crumb.settings.debug:
            from pprint import pprint
            print('execu graph is>')
            pprint(nodes_seq)
        return nodes_seq
    
    def run(self, input=None):
        self.last_execution_seq = self._compute_execution_seq()

        # these will go to the slicer
        pre_computed_results = {} #{(node_name, node_input): value}
        _missing_input = list() # in case something is missing
        for name, data in self._input_mapping.items():
            for node_name, node_input in data.items():
                if not name in input:
                    _missing_input.append(name)
                else:
                    if crumb.settings.debug:
                        print('slicer will get --->', (node_name, node_input[0]))
                    pre_computed_results[(node_name, node_input[0])] = input[name]
        if len(_missing_input) > 0:
            raise RuntimeError(f'missing inputs to Slice {self}, add variables: "{_missing_input}"')

        # print(self.last_execution_seq)
        te = get_slicer()
        results = te.add_work(task_seq=self.last_execution_seq, inputs_required=pre_computed_results)

        if crumb.settings.debug:
            print('results of slice execution are:', results)

        # populated nodes with output if needed
        for node in self.nodes.values():
            node = node['node']
            if node in self.last_execution_seq: # node was executed
                if not node.name in results:
                    raise RuntimeError('expected result to be in here but is not') #TODO: possibly this can become a warning
                else:
                    if node.save_exec:
                        node.last_exec = results[node.name]
        
        # obtain output for this slice:
        results_to_return = dict()
        for output_name, (node_name, node_output_name) in self._output_mapping.items():
            results_to_return[output_name] = results[node_name][node_output_name]

        return results_to_return

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
        self._graph_checked = False

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
        self._output_mapping[name] = None
        self._graph_checked = False

    def remove_output(self, name):
        """
        Remove Slice output
        @param name: name
        """
        self._check_output_exists(name, check_mapping=True) # if doesn't exist or in mapping not good to remove
        self.output.pop(name)
        self._output_mapping.pop(name)
    #

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

        node = self.nodes[node_name]['node']
        if self.input[name] != node.get_input_type(node_input):
            raise RuntimeError(f'"{name}" has got different type than input for node "{node_name}" (input: {node_input}). types are: "{self.input[name]}" and "{node.input[node_input]}"')
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
        self._input_mapping[name][node_name].remove(node_input)
        if len(self._input_mapping[name][node_name]) == 0:
            self._input_mapping[name].pop(node_name)
        self._graph_checked = False

    def add_output_mapping(self, name, node_name, node_output):
        """
        Add a mapping between a Node (defined within the node) and the Slice output
        @param name: the name of the output
        @param node_name: the name of the node
        @param node_output: the name of the node output
        """
        self._check_output_exists(name, check_mapping=True)
        self._check_node_exists(node_name, node_output)
        node = self.nodes[node_name]['node']
        if self.output[name] != node.get_output_type(node_output):
            raise RuntimeError(f'"{name}" has got different type than output for node "{node_name}" (output {node_output}). types are: "{self.output[name]}" and "{node.output[node_output]}"')
        if self._output_mapping[name] is None:
            self._output_mapping[name] = (node_name, node_output)

    def remove_output_mapping(self, name, node_name, node_output):
        """
        Remove mapping between Node and Slice output
        @param name: name of the output
        @param node_name: name of the node
        @param node_output: name of the node output
        """
        self._check_output_exists(name, check_mapping=False)
        if node_name != self._output_mapping[name][0]:
            raise RuntimeError(f'"{node_name}" not in output mapping')
        if node_output != self._output_mapping[name][1]:
            raise RuntimeError(f'another element was in the output, not "{node_output}"')
        self._output_mapping[name] = None
        self._graph_checked = False
    #

    # link
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
        A = self.nodes[nodeA]['node']
        B = self.nodes[nodeB]['node']
        A.add_output(this_output_name=nodeA_output, other_node=B, other_node_variable=nodeB_input)
        B.add_input(this_variable=nodeB_input, other_node=A, other_node_name=nodeA_output)

    def remove_link(self, nodeA, nodeA_output, nodeB, nodeB_input):
        self._check_node_exists(nodeA, node_output=nodeA_output)
        self._check_node_exists(nodeB, node_input=nodeB_input)
        A = self.nodes[nodeA]['node']
        B = self.nodes[nodeB]['node']
        A.remove_output(this_output_name=nodeA_output, other_node=B, other_node_variable=nodeB_input)
        B.remove_input(this_variable=nodeB_input)
        self._graph_checked = False
    #

    def __repr__(self):
        return f'{self.__class__.__name__} at {hex(id(self))} with {len(self.crumbs)} crumbs'

    def __str__(self):
        return self.__repr__()    

    # json save load
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
                'crumb': j['crumb'].to_json()
            } for i, j in self.crumbs.items()} if self.crumbs else {}
        }
        return json.dumps(this_structure)

    def from_json(self, json_str):
        json_str = json.loads(json_str)
        if json_str['version'] > __slicer_version__:
            raise ImportError('imported file has a higher version')
        self.version = __slicer_version__
        self.name = json_str['slice_name']
        
        self.input = {i:ast.literal_eval(j) for i,j in json_str['input']['objects'].items()} if json_str['input']['objects'] else {}
        self._input_mapping = json_str['input']['mapping']
        self.output = {i:ast.literal_eval(j) for i,j in json_str['output']['objects'].items()} if json_str['output']['objects'] else {}
        self._output_mapping = json_str['output']['mapping']

        self.crumbs = {i:{
            'crumb': Crumb.create_from_json(j['crumb'])
        } for i, j in json_str['crumbs'].items()} if json_str['crumbs'] else {}

    def save(self, path, overwrite=False):
        if not overwrite:
            if os.path.exists(path):
                raise FileExistsError(f'File {path} already exists. Use parameter "overwrite" to replace.')
        with open(path, 'w') as of:
            of.write(self.to_json)

    def load(self, path):
        with open(path) as f:
            self.from_json(f.read())
    