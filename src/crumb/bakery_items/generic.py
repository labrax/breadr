"""
Module generic
Definition of generic class BakeryItem
"""
from typing import Optional, Dict, Union, Any, List
from crumb.node import Node


class BakeryItem:
    """
    Generic definition of BakeryItem.
    """
    def __init__(self, name: str, input: Optional[Dict[str, type]], output: Union[type, Dict[str, type], None]):
        self.name = name
        self.input = input  # format is {'name': <type>}
        self.output = output  # this will look different depending on the class
        self.is_used_by: List[Node] = []  # list of nodes

    def run(self, input: Dict[str, Any]) -> Any:
        """
        Run this BakeryItem
        @param input: dict() with required inputs
        """
        raise NotImplementedError()

    def to_json(self) -> str:
        """
        Return this BakeryItem as a json string
        """
        raise NotImplementedError()

    def from_json(self, json_str) -> None:
        """
        Load this BakeryItem with definitions from a json string
        @param json_str
        """
        raise NotImplementedError()

    def load_from_file(self, filepath, this_name) -> None:
        """
        Load this BakeryItem with definitions from a python source file
        @param filepath: the file
        @param this_name: the name of this BakeryItem (as in the file)
        """
        raise NotImplementedError

    def reload(self) -> None:
        """
        Reload the information in this BakeryItem based on its filename
        """
        raise NotImplementedError()

    def add_node_using(self, node) -> None:
        """
        Identify that this BakeryItem is being used in a node
        @param node: obj
        """
        self.is_used_by.append(node)

    def remove_node_using(self, node) -> None:
        """
        Identify that this BakeryItem stopped being used in a node
        @param node: obj
        """
        self.is_used_by.remove(node)

    def get_nodes_using(self) -> list:
        """
        Return list of nodes using this BakeryItem
        """
        return self.is_used_by

    def is_being_used(self) -> bool:
        """
        Return bool indicating if this BakeryItem is being used
        """
        return len(self.is_used_by) > 0
