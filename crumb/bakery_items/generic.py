
class BakeryItem:
    def __init__(self, name, input, output):
        self.name = name
        self.input = input
        self.output = output
    
    def run(self, input):
        raise NotImplementedError()

    def to_json(self):
        raise NotImplementedError()

    def from_json(self, json_str):
        raise NotImplementedError()

    def load_from_file(self, filepath, this_name):
        raise NotImplementedError

    def reload(self):
        raise NotImplementedError()
