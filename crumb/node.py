
import time


class Node:
    __node_mapping_definition = dict()
    __node__instances = dict()

    def __init__(self, bakery_item, name=None):
        """
        Create a graph node.
        @param bakery_item: Slice or Crumb object
        @param name: name of the node; if None is id(self)
        """
        self.name = Node._get_unique_node_name(bakery_item.name, name)
        Node._set_node(self.name, self)
        self.bakery_item = bakery_item
        self.bakery_item.add_node_using(self)
        self.save_exec = True
        self.last_exec = {}

        if self.bakery_item.input:
            self.input = {i:None for i in self.bakery_item.input.keys()} # format is {'input name': ('other Node', 'other node name')} # each input
        else:
            self.input = {}

        if self.bakery_item.output:
            if self.bakery_item.__class__.__name__ == 'Slice':
                self.output = {i:dict() for i in self.bakery_item.output.keys()} # format is {'output name': {'other Node': [other node name, ...]}} # multiple output
            elif self.bakery_item.__class__.__name__ == 'Crumb':
                self.output = {None:dict()}
            else:
                raise NotImplementedError(f'"{self.bakery_item.__class__.__name__}" is not implemented for node')

    def __repr__(self):
        return f'{self.__class__.__name__} at {hex(id(self))} ({self.n_links()} links): ({str(self.bakery_item)})'

    def __str__(self):
        return self.__repr__()

    @classmethod
    def _set_node(cls, node_name, instance):
        cls.__node__instances[node_name] = instance

    @classmethod
    def _get_node(cls, node_name):
        return cls.__node__instances[node_name]

    @classmethod
    def _get_new_node_name(cls, bakery_item_name):
        """
        Generates new name for a node
        @param bakery_item_name: bakery item used
        """
        while True: # this should not need to loop
            newname = f'{bakery_item_name}.{time.time_ns()}'
            if not newname in cls.__node_mapping_definition:
                break
        cls.__node_mapping_definition[newname] = newname
        return newname

    @classmethod
    def _get_node_mapping(cls, old_name):
        """
        Returns the new name for an old node
        @param old_name
        """
        return cls.__node_mapping_definition[old_name]

    @classmethod
    def _get_unique_node_name(cls, bakery_item_name, proposed_name=None):
        """
        Assists the creation of new node names for old ones
        @param bakery_item_name: name for the bakery item attached
        @param proposed_name: previous name
        """
        if proposed_name is None:
            return cls._get_new_node_name(bakery_item_name)
        else:
            if proposed_name in cls.__node_mapping_definition:
                return cls.__node_mapping_definition[proposed_name]
            else:
                newname = cls._get_new_node_name(bakery_item_name)
                cls.__node_mapping_definition[proposed_name] = newname
                return newname

    def links_from_json(self, json_str):
        for input_name, other_node_data in json_str['input'].items():
            if not input_name in self.input:
                raise ValueError(f'Invalid input_name "{input_name}". It is not in this input!')
            if other_node_data is None:
                self.input[input_name] = None
            else:
                other_node_name, other_node_output_name = other_node_data
                other_node = Node._get_node(Node._get_node_mapping(other_node_name))
                self.input[input_name] = (other_node, other_node_output_name)
        
        for output_name, other_node_data in json_str['output'].items():
            if output_name == 'null':
                output_name = None
            for other_node_name, other_node_input_names in other_node_data.items():
                if not output_name in self.output:
                    raise ValueError(f'Invalid output_name "{output_name}". It is not in this output!')
                other_node = Node._get_node(Node._get_node_mapping(other_node_name))
                self.output[output_name][other_node] = other_node_input_names

    def links_to_json(self):
        this_structure = {'input': dict(), 'output': dict()}
        for input_name, other_node_data in self.input.items():
            if other_node_data is None:
                this_structure['input'][input_name] = None
            else:
                other_node, other_node_output_name = other_node_data
                this_structure['input'][input_name] = other_node.name, other_node_output_name
        
        for output_name, other_node_data in self.output.items():
            for other_node, other_node_input_names in other_node_data.items():
                if not output_name in this_structure['output']:
                    this_structure['output'][output_name] = dict()
                this_structure['output'][output_name][other_node.name] = other_node_input_names
        return this_structure

    def n_links_in(self):
        """
        Returns number of links to the input of this node
        """
        N = 0
        for i in self.input.values():
            if i is not None:
                N += 1
        return N

    def n_links_out(self):
        """
        Returns number of links from the output of this node
        """
        N = 0
        for i in self.output.values():
            if i is not None and i:
                N += 1
        return N

    def n_links(self):
        """
        Returns total number of links from n_links_in() + n_links_out()
        """
        return self.n_links_in() + self.n_links_out()

    def has_links(self):
        """
        Returns boolean indicating if this node has links
        """
        if self.n_links() > 0:
            return True
        return False

    def get_input_type(self, name):
        """
        Returns the type of this node input
        @param name: input name
        """
        if self.bakery_item.__class__.__name__ == 'Slice':
            self.bakery_item.input[name]
        elif self.bakery_item.__class__.__name__ == 'Crumb':
            return self.bakery_item.input[name]
        else:
            # this code should never run as error already in __init__
            raise NotImplementedError(f'"{self.bakery_item.__class__.__name__}" is not implemented for node')

    def get_output_type(self, name):
        """
        Returns the type of this node output
        @param name: output name
        """
        if self.bakery_item.__class__.__name__ == 'Slice':
            self.bakery_item.output[name]
        elif self.bakery_item.__class__.__name__ == 'Crumb':
            return self.bakery_item.output
        else:
            # this code should never run as error already in __init__
            raise NotImplementedError(f'"{self.bakery_item.__class__.__name__}" is not implemented for node')

    def _validate_input(self, target):
        """
        Checks if a a name in input
        @param target: what we looking for
        """
        if not target in self.input:
            raise RuntimeError(f'variable "{target}" wanted not in input')

    def _validate_output(self, other_node, other_node_variable):
        """
        Checks if a a name in output
        @param target: what we looking for
        """
        if not other_node_variable in other_node.input:
            raise RuntimeError(f'variable "{other_node_variable}" wanted not in input of "{other_node}"')

    def add_input(self, this_variable, other_node, other_node_name):
        """
        Adds another node to this node input
        @param this_variable: variable in my input
        @param other_node: the other node
        @param other_node_name: the name of the variable outputted by the other node
        """
        self._validate_input(this_variable)
        if self.input[this_variable] is not None:
            raise RuntimeError(f'variable "{this_variable}" is already defined')
        if not other_node_name in other_node.output:
            raise RuntimeError(f'output "{this_variable}" not in "{other_node}"')
        self.input[this_variable] = (other_node, other_node_name)

    def remove_input(self, this_variable):
        """
        Removes the links from another node to this input
        @param this_variable: the name of the input
        """
        self._validate_input(this_variable)
        if self.input[this_variable] is None:
            raise RuntimeError(f'variable {this_variable} is already undefined')
        self.input[this_variable] = None

    def add_output(self, this_output_name, other_node, other_node_variable):
        """
        Adds another node to this node output
        @param this_variable: variable in my output
        @param other_node: the other node
        @param other_node_name: the name of the variable inputted by the other node
        """
        self._validate_output(other_node, other_node_variable)
        if not this_output_name in self.output:
            raise RuntimeError(f'output {this_output_name} wanted not in output')
        if not other_node in self.output[this_output_name]:
            self.output[this_output_name][other_node] = list()
        self.output[this_output_name][other_node].append(other_node_variable)

    def remove_output(self, this_output_name, other_node, other_node_variable):
        """
        Removes another node to this node output
        @param this_output_name: variable in my output
        @param other_node: the other node
        @param other_node_name: the name of the variable inputted by the other node
        """
        if not other_node in self.output[this_output_name]:
            raise RuntimeError(f'"{other_node}" is not in our list of outputs')
        self.output[this_output_name][other_node].remove(other_node_variable)

    def run(self, input):
        """
        Return the output for the underlying bakery item element
        @param input: dict() with elements as needed, empty dict if not required
        """
        _ret = self.bakery_item.run(input)
        
        if self.bakery_item.__class__.__name__ == 'Slice':
            ret = _ret
        elif self.bakery_item.__class__.__name__ == 'Crumb':
            ret = {None:_ret}
        else:
            # this code should never run as error already in __init__
            raise NotImplementedError(f'"{self.bakery_item.__class__.__name__}" is not implemented for node')

        if self.save_exec:
            self.last_exec = ret

        return ret
        