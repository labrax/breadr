"""
Module Slicer
Definition for the Slicer class with the generic definition of an executor for BakeryItems.
"""
from typing import Union, TypedDict, List, Dict, Tuple, Any, Optional
from crumb.node import Node


class TaskDependencies(TypedDict):
    """Definition for sequence of tasks"""
    node: Node
    deps: List[str]


class TaskToBeDone(TypedDict):
    """Definition for a task pending"""
    node: Optional[Node]
    input: Dict[str, Any]


class Slicer:
    """
    Virtual definition for graph executors
    """
    TASK_EXECUTOR_INSTANCE = None

    def reset(self) -> None:
        """
        Reset the executor. Stops the queue and cancel jobs
        """
        raise NotImplementedError()

    def add_work(self, task_seq: List[TaskDependencies], inputs_required: Dict[Tuple[str, str], Any] = None) -> Union[Dict[str, Any], Any]:
        """
        Add tasks that need to be executed
        @param task_seq: format is: {'node': node_id, 'deps': [node_id_1, node_id_2, ...]}
        @param inputs_required: format is {(node_name, node_input): value}
        """
        raise NotImplementedError()

    def kill(self) -> None:
        """Stop the current executor"""
        return
