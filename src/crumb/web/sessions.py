"""Store the different files open"""

from collections import deque
import os
from typing import Dict, Tuple, Any

from crumb.web.node_definitions import get_input_definition, get_output_definition, get_node_definition
from crumb.bakery_items.slice import NodeRepresentation, Slice
from crumb.settings import Settings


class FileState:
    """A file with its slice etc"""
    def __init__(self, filepath):
        self.slice: Slice = None
        self.node_counter = 0
        self.filepath = filepath
        self.mapping_id_element = {}  # maps UI node ids to the internal nodes
        self.bakery_items_available = {}  # from the locally-available files
        self.translation = (0, 0)
        self.zoom_level = 0
        self.node_position = {}

        if os.path.exists(filepath):
            self.load_from_file(filepath)
            self.node_counter = len(self.slice.nodes)
        else:
            self.slice = Slice(name=os.path.basename(self.filepath))

    def load_from_file(self, path):
        """Load a slice from a file"""
        # get any meta-data from crumb web
        # load every node
        # load every connection
        raise NotImplementedError

    def send_batch(self):
        """Dispatches the local definitions in a single dict"""
        raise NotImplementedError

    def refresh_list(self):
        """Reloads the list of functions available"""
        base_folder = os.path.dirname(self.filepath)

        files = []
        folders = deque([base_folder])
        while len(folders) > 0:
            current_folder = folders.popleft()
            for i in os.listdir(current_folder):
                if Settings.WEB_SKIP_HIDDEN and (i[0] == '.' or i[0] == '_'):
                    continue
                if os.path.isfile(i) and i.split('.')[-1] in Settings.WEB_EXTENSIONS:
                    files.append(os.path.join(current_folder, i))
                elif not os.path.isfile(i) and Settings.WEB_EXPLORE_SUBFOLDERS:
                    folders.append(os.path.join(current_folder, i))

        raise NotImplementedError

    def get_function_list(self):
        """Send the list of functions available"""
        self.refresh_list()
        sections = [{'name': 'Basics', 'code': 'basics',
                    'functions': [{'type_identifier': 'input_element', 'name': ' Input', 'icon': 'fa-solid fa-arrow-right-to-bracket'},
                                  {'type_identifier': 'output_element', 'name': ' Output', 'icon': 'fa-solid fa-arrow-right-from-bracket'}]},
                    {'name': 'Crumbs', 'code': 'crumbs',
                    'functions': [{'type_identifier': 'multiple_element', 'name': ' AAA', 'icon': 'fas fa-code'},
                                  {'type_identifier': 'multiple_element', 'name': ' BBB', 'icon': 'fas fa-code'},
                                  {'type_identifier': 'multiple_element', 'name': ' CCC', 'icon': 'fas fa-code'}]}
                    ]
        return sections

    def save(self):
        """Calls the slice to be saved"""
        raise NotImplementedError

    def setParameter(self, node: int, name: str, type: str):
        """Rename an input"""
        # check if we good changing? aka: anything connected here? no duplicates?
        raise NotImplementedError

    def run(self):
        """Run the output for all the nodes"""
        raise NotImplementedError

    def translate(self, x, y):
        """Sets the translation for this execution"""
        self.translation = (x, y)

    def zoom(self, z):
        """Sets the zoom for the element"""
        self.zoom_level = z

    def move_node(self, id, x, y):
        """Set a node position"""
        self.node_position[id] = (x, y)

    def addNode(self, name, pos_x, pos_y) -> dict:
        """Add a node if available in the bakery_items list"""
        nnode: Any[NodeRepresentation, Tuple(str, str)] = None
        if name == 'input_element':
            while True:
                try:
                    nname = f'input_{self.node_counter}'
                    self.slice.add_input(name=nname, type=int)
                    nnode = ('input', nname)
                    ret = get_input_definition(self.node_counter, pos_x, pos_y, nname)
                    break
                except RuntimeError:
                    self.node_counter += 1
        elif name == 'output_element':
            while True:
                try:
                    nname = f'output_{self.node_counter}'
                    self.slice.add_output(name=nname, type=int)
                    nnode = ('output', nname)
                    ret = get_output_definition(self.node_counter, pos_x, pos_y, nname)
                    break
                except RuntimeError:
                    self.node_counter += 1
        elif name in self.bakery_items_available:
            if name not in self.slice.bakery_items:
                self.slice.add_bakery_item(name=name, bakery_item=self.bakery_items_available[name])
            nnode = self.slice.add_node(name)

            icon_str = "fas fa-code-branch"  # TODO
            inputs = self.slice.nodes[nnode]['node'].input
            outputs = self.slice.nodes[nnode]['node'].output
            description = "\n\n\n\n"  # TODO
            name = self.slice.bakery_items[name]['bakery_item'].name
            ret = get_node_definition(self.node_counter, name, pos_x, pos_y, inputs, outputs, icon=icon_str, node_description=description)
        else:
            raise RuntimeError('Crumb/Slice not defined!')

        self.node_position[name] = (pos_x, pos_y)
        self.mapping_id_element[self.node_counter] = nnode  # slice new node
        self.node_counter += 1
        return ret

    def removeNode(self, id):
        """Remove a node (if possible"""
        raise NotImplementedError

    def addConnection(self, id_output, id_input, output_class, input_class):
        """Adds a connection between two nodes (if possible)"""
        raise NotImplementedError

    def removeConnection(self, class_list):
        """Remove a connection between two nodes (if possible)"""
        raise NotImplementedError


class SessionStore:
    """All the stored sessions"""
    file_to_data: Dict[str, FileState] = {}

    @classmethod
    def get_file(cls, filepath):
        if filepath not in cls.file_to_data:
            cls.file_to_data[filepath] = FileState(filepath)
        return cls.file_to_data[filepath]
