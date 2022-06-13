"""Single-threaded task executor"""
from typing import Dict, Any, List, Union, Tuple

import crumb.settings
from crumb.node import Node
from .generic import Slicer, TaskDependencies, TaskToBeDone


class SingleSlicer(Slicer):
    """
    Executes the slices with a single-process approach.
    This is useful when there are not many operations, or a few heavy ones.
    The functions are not reloaded, and can be created from inside classes, or other functions.
    """
    TASK_EXECUTOR_INSTANCE = None

    def __new__(cls):
        if cls.TASK_EXECUTOR_INSTANCE is None:
            cls.TASK_EXECUTOR_INSTANCE = super().__new__(cls)
            cls.TASK_EXECUTOR_INSTANCE.reset()
        return cls.TASK_EXECUTOR_INSTANCE

    def reset(self):
        # ready for execution
        # [{'node': node, 'input': {name': value}}]
        self.tasks_to_be_done: List[TaskToBeDone] = []
        # {node_name: {var: value}}
        self.results: Dict[str, Dict[str, Any]] = {}
        # {node_name: {var: value}}
        self.input_for_nodes: Dict[str, Dict[str, Any]] = {}
        # {node_name: node}
        self.node_waiting: Dict[str, Node] = {}
        # {deps: [node_name]}
        self.deps_to_nodes: Dict[str, List[str]] = {}
        # if node not in here it means dependencies were solved and executed
        # {node_name: [deps]}
        self.nodes_to_deps: Dict[str, List[str]] = {}

    def _exec(self) -> None:
        while len(self.tasks_to_be_done) > 0:
            # get first in the queue
            task = self.tasks_to_be_done.pop(0)
            # get its name
            just_exec_node_name = task['node'].name
            # collect its results
            self.results[just_exec_node_name] = task['node'].run(task['input'])
            if just_exec_node_name in self.deps_to_nodes:
                # get these dependencies
                for node_name in self.deps_to_nodes[just_exec_node_name]:
                    # remove dependency for the task finished
                    self.nodes_to_deps[node_name].remove(just_exec_node_name)
                    # if there are no more dependencies prepare it to run
                    if len(self.nodes_to_deps[node_name]) == 0:
                        self.nodes_to_deps.pop(node_name)
                        # collect input for node
                        node = self.node_waiting[node_name]
                        # get all inputs - they are done
                        collected_inputs = {}
                        for input_name, (previous_node, other_node_input) in node.input.items():
                            if crumb.settings.DEBUG_VERBOSE:
                                print('adding to queue>', input_name, previous_node, other_node_input)
                            collected_inputs[input_name] = self.results[previous_node.name][other_node_input]
                        self.input_for_nodes[node_name] = collected_inputs
                        # remove from waiting list
                        self.node_waiting.pop(node_name)
                        # send for execution
                        self.tasks_to_be_done.append({'node': node, 'input': self.input_for_nodes[node_name]})
                        self.input_for_nodes.pop(node_name)  # we can clean this as it was already sent

    def add_work(self, task_seq: List[TaskDependencies], inputs_required: Dict[Tuple[str, str], Any] = None) -> Union[Dict[str, Any], Any]:
        """
        Add tasks that need to be executed
        @param task_seq: format is: {'node': node_id, 'deps': [node_id_1, node_id_2, ...]}
        @param inputs_required: format is {(node_name, node_input): value}
        """
        # if some nodes require some input add them to the relation first
        if inputs_required is not None:
            for (node_name, node_input), value in inputs_required.items():
                if node_name not in self.input_for_nodes:
                    self.input_for_nodes[node_name] = {}
                self.input_for_nodes[node_name][node_input] = value
        # compute nodes with node-node dependencies
        for task_element in task_seq:
            node, deps = task_element['node'], task_element['deps']
            if len(deps) == 0:
                if node.name not in self.input_for_nodes:
                    self.tasks_to_be_done.append({'node': node, 'input': {}})
                else:
                    self.tasks_to_be_done.append({'node': node, 'input': self.input_for_nodes[node.name]})
                continue
            self.node_waiting[node.name] = node
            self.nodes_to_deps[node.name] = deps
            for dependency in deps:
                if dependency not in self.deps_to_nodes:
                    self.deps_to_nodes[dependency] = []
                self.deps_to_nodes[dependency].append(node.name)
        # showtime!
        self._exec()
        to_ret = {}
        for i in task_seq:
            to_ret[i['node'].name] = self.results[i['node'].name]
            self.results.pop(i['node'].name)  # results are not needed here
        return to_ret
