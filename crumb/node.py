

from pickletools import TAKEN_FROM_ARGUMENT4U


class Node:
    def __init__(self, bakery_item, name=None):
        if name is None:
            name = id(self)
        self.name = name
        self.bakery_item = bakery_item
        self.bakery_item.is_used = True

        if bakery_item.input:
            self.input = {i:None for i in bakery_item.input.keys()} # format is {'input name': ('other Node', 'other node name')} # single input
        else:
            self.input = {}

        if self.bakery_item.output:
            if self.bakery_item.__class__.__name__ == 'Slice':
                self.output = {i:dict() for i in self.bakery_item.output.keys()} # format is {'output name': {'other Node': [other node name]}} # multiple output
            elif self.bakery_item.__class__.__name__ == 'Crumb':
                self.output = {None:dict()}
            else:
                raise RuntimeError(f'"{self.bakery_item.__class__.__name__}" is not implemented for node')

    def n_links_in(self):
        N = 0
        for i in self.input.values():
            if i is not None:
                N += 1
        return N

    def n_links_out(self):
        N = 0
        for i in self.output.values():
            if i is not None:
                N += 1
        return N

    def n_links(self):
        return self.n_links_in() + self.n_links_out()

    def has_links(self):
        for i in self.output.values():
            if i is not None:
                return True
        for i in self.input.values():
            if i is not None:
                return True
        return False

    def get_input_type(self, name):
        if self.bakery_item.__class__.__name__ == 'Slice':
            self.bakery_item.input[name]
        elif self.bakery_item.__class__.__name__ == 'Crumb':
            return self.bakery_item.input[name]
        else:
            raise RuntimeError(f'"{self.bakery_item.__class__.__name__}" is not implemented for node')

    def get_output_type(self, name):
        if self.bakery_item.__class__.__name__ == 'Slice':
            self.bakery_item.output[name]
        elif self.bakery_item.__class__.__name__ == 'Crumb':
            return self.bakery_item.output
        else:
            raise RuntimeError(f'"{self.bakery_item.__class__.__name__}" is not implemented for node')

    def _validate_input(self, target):
        if not target in self.input:
            raise RuntimeError(f'variable "{target}" wanted not in input')

    def _validate_output(self, other_node, other_node_variable):
        if not other_node_variable in other_node.input:
            raise RuntimeError(f'variable "{other_node_variable}" wanted not in input of "{other_node}"')

    def add_input(self, this_variable, other_node, other_node_name):
        self._validate_input(this_variable)
        if self.input[this_variable] is not None:
            raise RuntimeError(f'variable "{this_variable}" is already defined')
        if not other_node_name in other_node.output:
            raise RuntimeError(f'output "{this_variable}" not in "{other_node}"')
        self.input[this_variable] = (other_node, other_node_name)

    def remove_input(self, this_variable):
        self._validate_input(this_variable)
        if self.input[this_variable] is None:
            raise RuntimeError(f'variable {this_variable} is already undefined')
        self.input[this_variable] = None

    def add_output(self, this_output_name, other_node, other_node_variable):
        self._validate_output(other_node, other_node_variable)
        if not this_output_name in self.output:
            raise RuntimeError(f'output {this_output_name} wanted not in output')
        if not other_node in self.output[this_output_name]:
            self.output[this_output_name][other_node] = list()
        self.output[this_output_name][other_node].append(other_node_variable)

    def remove_output(self, this_output_name, other_node, other_node_variable):
        if not other_node in self.output[this_output_name]:
            raise RuntimeError(f'"{other_node}" is not in our list of outputs')
        self.output[this_output_name][other_node].pop(other_node_variable)
        if len(self.output[this_output_name][other_node]) == 0:
            self.output[this_output_name].pop(other_node)
    
    def __repr__(self):
        return f'{self.__class__.__name__} at {hex(id(self))} ({self.n_links()} links): ({str(self.bakery_item)})'

    def __str__(self):
        return self.__repr__()
