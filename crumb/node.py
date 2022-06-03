

class Node:
    def __init__(self, crumb, name=None):
        if name is None:
            name = id(self)
        self.name = name
        self.crumb = crumb

        if crumb.input:
            self.input = {i:None for i in crumb.input.keys()} # format is {variable: other Node}
        else:
            self.input = {}
        self.output = dict() # format is {variable: {other Node: [other node name]}}

    def _validate_input(self, target):
        if target not in self.input:
            raise ValueError(f'variable "{target}" wanted not in input')

    def _validate_output(self, other_node, other_node_variable):
        if other_node_variable not in other_node.input:
            raise ValueError(f'variable "{other_node_variable}" wanted not in input of {other_node}')

    def add_input(self, this_variable, node):
        self._validate_input(this_variable)
        if self.input[this_variable] is not None:
            raise ValueError(f'variable {this_variable} is already defined')
        self.input[this_variable] = node

    def remove_input(self, this_variable):
        self._validate_input(this_variable)
        if self.input[this_variable] is None:
            raise ValueError(f'variable {this_variable} is already undefined')
        self.input[this_variable] = None

    def add_output(self, other_node, other_node_variable):
        self._validate_output(other_node, other_node_variable)
        if other_node not in self.output:
            self.output[other_node] = list()
        self.output[other_node].append(other_node_variable)

    def remove_output(self, other_node, other_node_variable):
        self._validate_output(other_node, other_node_variable)
        self.output[other_node].pop(other_node_variable)
        if len(self.output[other_node]) == 0:
            self.output.pop(other_node)
    
    def __repr__(self):
        return f'{self.__class__.__name__} - {hex(id(self))}: ({self.crumb.name})'

    def __str__(self):
        return self.__repr__()