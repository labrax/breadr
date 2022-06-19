
"""Slice
This module implements the class Slice, child of BakeryItem.

This class is a container that stores other BakeryItem.
The BakeryItems can be instanced into Nodes, and linked in different ways to run different pipelines.

This big class contains implementations for the main functionality needed:
- add/remove BakeryItems:
add and remove them based
- create instances Node that represent different BakeryItem operations
- input/output, their mappings, and link between Node:
relate the different Node and the input/output of this Slice
- serialiser and deserialiser to json, save and load
"""
import os
import json
from typing import Dict, List, Tuple, Optional, TypedDict, Any

from crumb import __slice_serializer_version__

from crumb.node import Node
from crumb.slicers.slicers import get_slicer
from crumb.bakery_items.crumb import Crumb
from crumb.bakery_items.generic import BakeryItem
from crumb.logger import LoggerQueue, log, logging


class NodeRepresentation(TypedDict):
    """Representation of Nodes ins Slice.nodes"""
    node: Node
    instance_of: str


class NodeDeps(TypedDict):
    """Representation of Node to be executed"""
    node: Node
    deps: list


class BakeryItemStore(TypedDict):
    """Representation of BakeryItem stored"""
    bakery_item: BakeryItem
    type: str


class Slice(BakeryItem):
    """
    Slice module, an instance of BakeryItem
    This module can adds other BakeryItem's, define input/output and get the output of running the models.
    """
    def __init__(self, name: str):
        # already defined here to maintain this definition throughout the code
        self.input: Dict[str, type] = {}
        self.output: Dict[str, type] = {}
        # in the case of slice, input and output are {'name': <type>}
        super().__init__(name, input={}, output={})
        self.version = __slice_serializer_version__
        # # an input to slice can go to multiple bakery_items
        # format: {'input_name': {'node name': ['Node input name']}}
        self._input_mapping: Dict[str, Dict[str, List[str]]] = {}
        # an output can come from a single bakery_item
        # format: {'output_name': ('node name', 'Node output name'])}
        self._output_mapping: Dict[str, Optional[Tuple[str, str]]] = {}
        # relation of all the bakeryitems added to this Slice
        # format: {'name given': {'bakery_item': bakery_item, 'type': class name of bakery item}}
        self.bakery_items: Dict[str, BakeryItemStore] = {}
        # relation of nodes with instances of BakeryItems
        # format: {'identifier': {'node': Node, 'instance_of': 'bakery item name'}}
        self.nodes: Dict[str, NodeRepresentation] = {}
        # whether the graph has been checked for execution before, and it is expect to run fine
        self._graph_checked: bool = False
        # these are the nodes that require input, if _graph_checked is True, they are in _input_mapping
        # format is {node: {'node var': 'node var type'}}
        self._required_input: Optional[Dict[Node, Dict[str, type]]] = None
        self.last_execution_seq: Optional[List[NodeDeps]] = None
        self.filepath: Optional[str] = None

    def __repr__(self):
        return f'{self.__class__.__name__} at {hex(id(self))} with {len(self.bakery_items)} crumbs and {len(self.nodes)} nodes'

    def __str__(self):
        return self.__repr__()

    def from_json(self, json_str: str) -> None:
        json_obj = json.loads(json_str)
        if json_obj['version'] > __slice_serializer_version__:
            raise ImportError('Imported file has a higher version')
        self.version = __slice_serializer_version__
        self.name = json_obj['slice_name']
        # if it is a loaded/saved Slice lets reload from the original file
        if 'filepath' in json_obj:
            self.load_from_file(json_obj['filepath'], this_name=json_obj['slice_name'])
        else:  # if it is not we'll need to load all the inside bits
            # check types
            def _type_eval(type_str):
                """
                eval is naturally unsafe. Checks were made to improve security
                """
                if not all(i.isalnum() or (i == '.') for i in type_str):
                    raise RuntimeError(f'Invalid type name "{type_str}"!')
                type_evaluated = eval(type_str)
                if type_evaluated.__class__.__name__ == 'type':
                    return type_evaluated
                else:
                    raise RuntimeError(f'Invalid type name "{type_str}"!')
            # input/output
            self.input = {i: _type_eval(j) for i, j in json_obj['input']['objects'].items()} if json_obj['input']['objects'] else {}
            self.output = {i: _type_eval(j) for i, j in json_obj['output']['objects'].items()} if json_obj['output']['objects'] else {}
            # start bakery items

            def _create_bi_from_instance(json_str: str, type: type):
                if type == 'Crumb':
                    return Crumb.create_from_json(json_str)
                if type == 'Slice':
                    current_slice = Slice(name='_dummy')
                    current_slice.from_json(json_str)
                    return current_slice
                raise NotImplementedError('Can only handle Crumb and Slice objects')
            self.bakery_items = {i: {
                'bakery_item': _create_bi_from_instance(j['bakery_item'], j['type']),
                'type': j['type']
            } for i, j in json_obj['bakery_items'].items()} if json_obj['bakery_items'] else {}
            self.nodes = {}
            # first start the nodes
            for node_name, node_data in json_obj['nodes'].items():
                instance_of: str = node_data['instance_of']
                save_exec, last_exec = node_data['save_exec'], node_data['last_exec']
                new_node: Node = Node(bakery_item=self.bakery_items[instance_of]['bakery_item'], name=node_name)
                new_node.last_exec = last_exec
                new_node.save_exec = save_exec
                self.nodes[new_node.name] = {'node': new_node, 'instance_of': instance_of}
            # then start the links
            for node_name, node_data in json_obj['nodes'].items():
                link_str = node_data['link_str']
                new_node = Node.get_node(Node.get_node_mapping(node_name))
                new_node.links_from_json(link_str)
            # translate the name of the nodes
            self._input_mapping = {}
            for input_name, data in json_obj['input']['mapping'].items():
                self._input_mapping[input_name] = {}
                for node_name, node_inputs in data.items():
                    self._input_mapping[input_name][Node.get_node_mapping(node_name)] = node_inputs
            self._output_mapping = {}
            for output_name, (node_name, node_output_name) in json_obj['output']['mapping'].items():
                self._output_mapping[output_name] = (Node.get_node_mapping(node_name), node_output_name)

    def to_json(self, tofile: bool = False) -> str:
        if self.filepath and not tofile:
            this_structure = {
                'slice_name': self.name,
                'version': __slice_serializer_version__,
                'filepath': self.filepath
            }
        else:
            this_structure = {
                'slice_name': self.name,
                'version': __slice_serializer_version__,
                'input': {
                    'objects': {i: j.__name__ for i, j in self.input.items()} if self.input else {},
                    'mapping': self._input_mapping
                },
                'output': {
                    'objects': {i: j.__name__ for i, j in self.output.items()} if self.output else {},
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

    def load_from_file(self, filepath: str, this_name: str = None) -> None:
        """Load the current object from a file using the from_json method"""
        with open(filepath, mode='r', encoding="utf-8") as open_file:
            self.from_json(open_file.read())
        self.filepath = filepath

    def save_to_file(self, path: str, overwrite: bool = False) -> None:
        """Save the current object to a file using the to_json method"""
        if not overwrite:
            if os.path.exists(path):
                raise FileExistsError(f'File {path} already exists. Use parameter "overwrite" to replace.')
        with open(path, mode='w', encoding="utf-8") as open_file:
            open_file.write(self.to_json(tofile=True))
        self.filepath = path

    def reload(self):
        for i in self.bakery_items.values():
            i['bakery_item'].reload()

    def run(self, input: Dict[str, Any] = None) -> Dict[str, Any]:
        if input is None:
            input = {}
        self.last_execution_seq = self._compute_execution_seq()
        # these will go to the slicer
        pre_computed_results = {}  # {(node_name, node_input): value}
        _missing_input = []  # in case something is missing
        for name, data in self._input_mapping.items():
            for node_name, node_input in data.items():
                if name not in input:
                    _missing_input.append(name)
                else:
                    log(LoggerQueue.get_logger(), f'slicer will get ---> {(node_name, node_input[0])}', logging.DEBUG)
                    pre_computed_results[(node_name, node_input[0])] = input[name]
        if len(_missing_input) > 0:
            raise RuntimeError(f'Missing inputs to Slice {self}, add variables: "{_missing_input}"')
        _extra_input = []
        _input_not_used = []
        for name in input.keys():
            if name not in self.input.keys():
                _extra_input.append(name)
            if name in self.input.keys() and len(self._input_mapping[name]) == 0:
                _input_not_used.append(name)
        if len(_extra_input) > 0:
            log(LoggerQueue.get_logger(), f'{self} has no inputs: "{_extra_input}"', logging.WARNING)
        if len(_input_not_used) > 0:
            log(LoggerQueue.get_logger(), f'{self} is not using inputs: "{_input_not_used}"', logging.WARNING)
        # print(self.last_execution_seq)
        task_executor = get_slicer()
        results = task_executor.add_work(task_seq=self.last_execution_seq, inputs_required=pre_computed_results)
        log(LoggerQueue.get_logger(), f'Results of slice execution are: {results}', logging.DEBUG)
        # obtain output for this slice:
        results_to_return = {}
        for output_name, (node_name, node_output_name) in self._output_mapping.items():
            results_to_return[output_name] = results[node_name][node_output_name]
        return results_to_return

    def add_bakery_item(self, name: str, bakery_item: BakeryItem) -> None:
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

    def add_node(self, bi_name: str) -> str:
        """Add node to graph and returns its name
        @param bi_name: the name of the BakeryItem of reference"""
        new_node = Node(self.bakery_items[bi_name]['bakery_item'])
        self.nodes[new_node.name] = {'node': new_node,
                                     'instance_of': bi_name}
        return new_node.name

    def remove_node(self, node_name: str) -> None:
        """Remove node from graph (only works if it is not linked)"""
        for i in self._input_mapping.values():
            if node_name in i:
                raise RuntimeError(f'Cannot remove "{node_name}", it is linked to input!')
        for j in self._output_mapping.values():
            if j is not None:
                if node_name in j:
                    raise RuntimeError(f'Cannot remove "{node_name}", it is linked to output!')
        if self.nodes[node_name]['node'].has_links():
            raise RuntimeError(f'Cannot remove "{node_name}", it is connected to other nodes!')
        self.nodes[node_name]['node'].bakery_item.remove_node_using(self.nodes[node_name]['node'])
        self.nodes.pop(node_name)

    def _check_input_exists(self, name: str, check_mapping: bool = True) -> None:
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

    def _check_output_exists(self, name: str, check_mapping: bool = True) -> None:
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

    def _check_node_exists(self, node_name: str, node_input: str = None, node_output: str = None) -> None:
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

    def _check_graph_circular(self) -> int:
        """Return number of components in graph while checking if it is circular"""
        if len(self.nodes) == 0:
            return 0
        # format is: {name of node: component id}
        visited: Dict[str, int] = {}
        max_it = 0
        for i, stack_start in enumerate(self.nodes.keys()):
            if stack_start in visited:
                continue
            stack = [stack_start]
            while len(stack) > 0:
                current = stack.pop(0)
                # for each {'output name': {node, ['input name', ...]}}
                for element_with_output in self.nodes[current]['node'].output.values():
                    # for each {node, [...]}
                    for out_node, _ in element_with_output.items():
                        if (out_node.name in visited) and (visited[out_node.name] == i):
                            raise RuntimeError(f'"{out_node.name}" already explored, graph is circular')
                        if out_node.name not in visited:
                            stack.append(out_node.name)
                            visited[out_node.name] = i
            max_it = i
        return max_it

    def _get_nodes_missing_input(self, only_in_output: bool = True) -> Dict[Node, Dict[str, type]]:
        stack: List[Node] = []
        if only_in_output:
            stack = [self.nodes[node]['node'] for node, _ in self._output_mapping.values()]
        else:
            stack = [i['node'] for i in self.nodes.values()]
        # format is {node: {'node var': 'node var type'}}
        input_undefined: Dict[Node, Dict[str, type]] = {}
        visited = set(stack)
        while len(stack) > 0:
            current = stack.pop(0)
            for inp, data in current.input.items():
                if data is None:
                    if current not in input_undefined:
                        input_undefined[current] = {}
                    input_undefined[current][inp] = current.bakery_item.input[inp]
                else:
                    other_node = data[0]
                    visited.add(other_node)
                    stack.append(other_node)
        # these are the inputs missing within the graph
        return input_undefined

    def _check_input_complete(self, only_in_output: bool = True) -> None:
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
            raise RuntimeError(f'Input is undefined for at least one node:\n"{err}"')

    def _check_graph(self) -> None:
        self._check_graph_circular()
        self._check_input_complete()
        self._graph_checked = True

    def _compute_execution_seq(self) -> List[NodeDeps]:
        if not self._graph_checked:
            self._check_graph()  # in case of error an exception will be raised
        # format is: [{'node': node_id, 'deps': [node_id_1, node_id_2, ...]}]
        nodes_seq: List[NodeDeps] = []
        # start from slice input
        for node in self.nodes.values():
            this: NodeDeps = {'node': node['node'], 'deps': []}
            for _, data in node['node'].input.items():
                if data is not None:  # if none comes from slice!
                    this['deps'].append(data[0].name)
            nodes_seq.append(this)
        log(LoggerQueue.get_logger(), 'execu graph is> {nodes_seq}', logging.DEBUG)
        return nodes_seq

    # slice input and output functions
    def add_input(self, name: str, type: type) -> None:
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

    def remove_input(self, name: str) -> None:
        """
        Remove Slice input
        @param name: name
        """
        # if doesn't exist or in mapping not good to remove
        self._check_input_exists(name, check_mapping=True)
        self.input.pop(name)
        self._input_mapping.pop(name)

    def add_output(self, name: str, type: type) -> None:
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

    def remove_output(self, name: str) -> None:
        """
        Remove Slice output
        @param name: name
        """
        self._check_output_exists(name, check_mapping=True)  # if doesn't exist or in mapping not good to remove
        self.output.pop(name)
        self._output_mapping.pop(name)
    #

    # mapping functions
    def add_input_mapping(self, name: str, node_name: str, node_input: str) -> None:
        """
        Add a mapping between a Node (defined within the node) and the Slice input
        @param name: name of the input
        @param node_name: name of the node
        @param node_input: name of the node input
        """
        # check for existance
        self._check_input_exists(name, check_mapping=False)
        self._check_node_exists(node_name, node_input=node_input)
        # check for types
        node = self.nodes[node_name]['node']
        if self.input[name] != node.get_input_type(node_input):
            raise RuntimeError(f'"{name}" has got different type than input for node "{node_name}" (input: {node_input}).'
                               + f'types are: "{self.input[name]}" and "{node.input[node_input]}"')
        if name not in self._input_mapping:
            self._input_mapping = {}
        if node_name not in self._input_mapping[name]:
            self._input_mapping[name][node_name] = []
        self._input_mapping[name][node_name].append(node_input)

    def remove_input_mapping(self, name: str, node_name: str, node_input: str) -> None:
        """
        Remove mapping between Node and Slice input
        @param name: name of the input
        @param node_name: name of the node
        @param node_input: name of the node input
        """
        self._check_input_exists(name, check_mapping=False)
        if node_name not in self._input_mapping[name]:
            raise RuntimeError(f'"{node_name} not in input mapping')
        self._input_mapping[name][node_name].remove(node_input)
        if len(self._input_mapping[name][node_name]) == 0:
            self._input_mapping[name].pop(node_name)
        self._graph_checked = False

    def add_output_mapping(self, name: str, node_name: str, node_output: str) -> None:
        """
        Add a mapping between a Node (defined within the node) and the Slice output
        @param name: the name of the output
        @param node_name: the name of the node
        @param node_output: the name of the node output
        """
        # check for existance
        self._check_output_exists(name, check_mapping=True)
        self._check_node_exists(node_name, node_output=node_output)
        # check for types
        node = self.nodes[node_name]['node']
        if self.output[name] != node.get_output_type(node_output):
            raise RuntimeError(f'"{name}" has got different type than output for node "{node_name}" (output {node_output}).'
                               + f' types are: "{self.output[name]}" and "{node.output[node_output]}"')
        if self._output_mapping[name] is None:
            self._output_mapping[name] = (node_name, node_output)

    def remove_output_mapping(self, name: str, node_name: str, node_output: str) -> None:
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
    def add_link(self, node_a: str, node_a_output: str, node_b: str, node_b_input: str) -> None:
        """
        Links two nodes
        @param nodeA: first node
        @param nodeA_output: first node output name
        @param nodeB: second node
        @param nodeB_output: second node output name
        """
        self._check_node_exists(node_a, node_output=node_a_output)
        self._check_node_exists(node_b, node_input=node_b_input)
        node_a_found = self.nodes[node_a]['node']
        node_b_found = self.nodes[node_b]['node']
        node_a_found.add_output(this_output_name=node_a_output, other_node=node_b_found, other_node_variable=node_b_input)
        node_b_found.add_input(this_variable=node_b_input, other_node=node_a_found, other_node_name=node_a_output)

    def remove_link(self, node_a: str, node_a_output: str, node_b: str, node_b_input: str) -> None:
        """
        Remove links between two nodes
        @param nodeA: first node
        @param nodeA_output: first node output name
        @param nodeB: second node
        @param nodeB_output: second node output name
        """
        self._check_node_exists(node_a, node_output=node_a_output)
        self._check_node_exists(node_b, node_input=node_b_input)
        node_a_found = self.nodes[node_a]['node']
        node_b_found = self.nodes[node_b]['node']
        node_a_found.remove_output(this_output_name=node_a_output, other_node=node_b_found, other_node_variable=node_b_input)
        node_b_found.remove_input(this_variable=node_b_input)
        self._graph_checked = False
