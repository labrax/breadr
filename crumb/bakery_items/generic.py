
class BakeryItem:
    def __init__(self, name, input, output):
        self.name = name
        self.input = input # format is {'name': <type>}
        self.output = output # this will look different depending on the class
        self.is_used_by = list() # list of nodes
    
    def run(self, input):
        """
        Runs this BakeryItem
        @param input: dict() with required inputs
        """
        raise NotImplementedError()

    def to_json(self):
        """
        Returns this BakeryItem as a json string
        """
        raise NotImplementedError()

    def from_json(self, json_str):
        """
        Load this BakeryItem with definitions from a json string
        @param json_str
        """
        raise NotImplementedError()

    def load_from_file(self, filepath, this_name):
        """
        Load this BakeryItem with definitions from a python source file
        @param filepath: the file
        @param this_name: the name of this BakeryItem (as in the file)
        """
        raise NotImplementedError

    def reload(self):
        """
        Reloads the information in this BakeryItem based on its filename
        """
        raise NotImplementedError()

    def add_node_using(self, node):
        """
        Identifies that this BakeryItem is being used in a node
        @param node: obj
        """
        self.is_used_by.append(node)

    def remove_node_using(self, node):
        """
        Identifies that this BakeryItem stopped being used in a node
        @param node: obj
        """
        self.is_used_by.remove(node)

    def get_nodes_using(self):
        """
        Returns list of nodes using this BakeryItem
        """
        return self.is_used_by

    def is_being_used(self):
        """
        Returns bool indicating if this BakeryItem is being used
        """
        return len(self.is_used_by) > 0
