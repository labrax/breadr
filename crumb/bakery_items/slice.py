
import itertools
from multiprocessing.sharedctypes import Value
import os
import json

import crumb.settings
from crumb import __slice_serializer_version__

from crumb.node import Node
from crumb.slicers.slicers import get_slicer
from crumb.bakery_items.crumb import Crumb
from crumb.bakery_items.generic import BakeryItem


class Slice(BakeryItem):
    def __init__(self, name):
        # in the case of slice, input and output are {'name': <type>}
        super().__init__(name, input=dict(), output=dict())
        self.version = __slice_serializer_version__

        self._input_mapping = dict() # {'input_name': {'node name': ['Node input name']}} # an input to slice can go to multiple bakery_items
        self._output_mapping = dict() # {'output_name': ('node name', 'Node output name'])} # an output can com from a single bakery_item
        
        self.bakery_items = dict() # {'name given': {'bakery_item': bakery_item, 'type': class name of bakery item}}
        self.nodes = dict() # {'identifier': {'node': Node, 'instance_of': 'bakery item name'}}

        self._graph_checked = False
        # these are the nodes that require input, if _graph_checked is True, they are in _input_mapping format is {node: {'node var': 'node var type'}}
        self._required_input = None
        self.last_execution_seq = None

    def __repr__(self):
        return f'{self.__class__.__name__} at {hex(id(self))} with {len(self.bakery_items)} crumbs'

    def __str__(self):
        return self.__repr__() 

    def from_json(self, json_str):
        json_str = json.loads(json_str)
        if json_str['version'] > __slice_serializer_version__:
            raise ImportError('Imported file has a higher version')
        self.version = __slice_serializer_version__
        self.name = json_str['slice_name']

        def _type_eval(type_str):
            """
            eval is naturally unsafe. Checks were made to improve security
            """
            if not all([i.isalnum() or (i == '.') for i in type_str]):
                raise RuntimeError(f'Invalid type name "{type_str}"!')
            else:
                ev = eval(type_str)
                if ev.__class__.__name__ == 'type':
                    return ev
                else:
                    raise RuntimeError(f'Invalid type name "{type_str}"!')

        self.input = {i:_type_eval(j) for i,j in json_str['input']['objects'].items()} if json_str['input']['objects'] else {}
        self.output = {i:_type_eval(j) for i,j in json_str['output']['objects'].items()} if json_str['output']['objects'] else {}

        def _create_bi_from_instance(json_str, type):
            if type == 'Crumb':
                return Crumb.create_from_json(json_str)
            elif type == 'Slice':
                s = Slice(name='_dummy')
                s.from_json(json_str)
                return s
            else:
                raise NotImplementedError('Can only handle Crumb and Slice objects')

        self.bakery_items = {i:{
            'bakery_item': _create_bi_from_instance(j['bakery_item'], j['type']),
            'type': j['type']
        } for i, j in json_str['bakery_items'].items()} if json_str['bakery_items'] else {}

        self.nodes = dict()
        # first start the nodes
        for node_name, node_data in json_str['nodes'].items():
            instance_of = node_data['instance_of']
            save_exec, last_exec = node_data['save_exec'], node_data['last_exec']
            n = Node(bakery_item=self.bakery_items[instance_of]['bakery_item'], name=node_name)
            n.last_exec = last_exec
            n.save_exec = save_exec
            self.nodes[n.name] = {'node': n,
                                  'instance_of': instance_of}
        # then start the links
        for node_name, node_data in json_str['nodes'].items():
            link_str = node_data['link_str']
            n = Node._get_node(Node._get_node_mapping(node_name))
            n.links_from_json(link_str)

        # translate the name of the nodes
        self._input_mapping = {}
        for input_name, data in json_str['input']['mapping'].items():
            self._input_mapping[input_name] = dict()
            for node_name, node_inputs in data.items():
                self._input_mapping[input_name][Node._get_node_mapping(node_name)] = node_inputs
        self._output_mapping = {}
        for output_name, (node_name, node_output_name) in json_str['output']['mapping'].items():
            self._output_mapping[output_name] = (Node._get_node_mapping(node_name), node_output_name)

    def to_json(self):
        this_structure = {
            'slice_name': self.name,
            'version': __slice_serializer_version__,
            'input': {
                'objects': {i:j.__name__ for i,j in self.input.items()} if self.input else {},
                'mapping': self._input_mapping
            },
            'output': {
                'objects': {i:j.__name__ for i,j in self.output.items()} if self.output else {},
                'mapping': self._output_mapping
            },
            'bakery_items': {i: {
                'bakery_item': j['bakery_item'].to_json(),
                'type': j['type']
            } for i, j in self.bakery_items.items()} if self.bakery_items else {},
            'nodes': {i: {
                'instance_of': j['instance_of'],
                'link_str': j['node'].links_to_json(),
                'save_exec': j['node'].save_exec,
                'last_exec': j['node'].last_exec
            } for i, j in self.nodes.items()}
        }
        return json.dumps(this_structure)

    def load_from_file(self, path):
        with open(path) as f:
            self.from_json(f.read())

    def save_to_file(self, path, overwrite=False):
        if not overwrite:
            if os.path.exists(path):
                raise FileExistsError(f'File {path} already exists. Use parameter "overwrite" to replace.')
        with open(path, 'w') as of:
            of.write(self.to_json)
    
    def reload(self):
        for i in self.bakery_items.values():
            i['bakery_item'].reload()

    def run(self, input=dict()):
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
            raise RuntimeError(f'Missing inputs to Slice {self}, add variables: "{_missing_input}"')

        # print(self.last_execution_seq)
        te = get_slicer()
        results = te.add_work(task_seq=self.last_execution_seq, inputs_required=pre_computed_results)

        if crumb.settings.debug:
            print('Results of slice execution are:', results)

        # obtain output for this slice:
        results_to_return = dict()
        for output_name, (node_name, node_output_name) in self._output_mapping.items():
            results_to_return[output_name] = results[node_name][node_output_name]

        return results_to_return

    def add_bakery_item(self, name, bakery_item):
        """
        Add bakery item to this Slice so it can be used
        @param name: name to be used here
        @param bakery_item: bakery_item name
        """
        if not isinstance(bakery_item, BakeryItem):
            raise ValueError(f'Object needs to be instance of class BakeryItem, it is "{bakery_item.__class__.__name__}"')
        if name in self.bakery_items:
            raise ValueError(f'A bakery item with name "{name}" is already in this Slice ({self.name})')
        self.bakery_items[name] = {'bakery_item': bakery_item,
                                   'type': bakery_item.__class__.__name__}

    def add_node(self, bi_name):
        n = Node(self.bakery_items[bi_name]['bakery_item'])
        self.nodes[n.name] = {'node': n,
                              'instance_of': bi_name}
        return n.name

    def remove_node(self, node_name):
        for i in self._input_mapping.values():
            if node_name in i:
                raise RuntimeError(f'Cannot remove "{node_name}", it is linked to input!')

        for i in self._output_mapping.values():
            if not i is None:
                if node_name in i:
                    raise RuntimeError(f'Cannot remove "{node_name}", it is linked to output!')

        if self.nodes[node_name]['node'].has_links():
            raise RuntimeError(f'Cannot remove "{node_name}", it is connected to other nodes!')
        
        self.nodes[node_name]['node'].bakery_item.remove_node_using(self.nodes[node_name]['node'])
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

    def _get_nodes_missing_input(self, only_in_output=True):
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
        input_undefined = self._get_nodes_missing_input(only_in_output=only_in_output)
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
            raise RuntimeError('Input is undefined for at least one node:\n"{}"'.format(err))

    def _check_graph(self):
        self._check_graph_circular()
        self._check_input_complete()
        self._graph_checked = True

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
            raise RuntimeError(f'Cannot remove: another element was in the output, not "{node_output}"')
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
        """
        Remove links between two nodes
        @param nodeA: first node
        @param nodeA_output: first node output name
        @param nodeB: second node
        @param nodeB_output: second node output name
        """
        self._check_node_exists(nodeA, node_output=nodeA_output)
        self._check_node_exists(nodeB, node_input=nodeB_input)
        A = self.nodes[nodeA]['node']
        B = self.nodes[nodeB]['node']
        A.remove_output(this_output_name=nodeA_output, other_node=B, other_node_variable=nodeB_input)
        B.remove_input(this_variable=nodeB_input)
        self._graph_checked = False
