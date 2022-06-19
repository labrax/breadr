"""Functions for multislicer processes"""
from queue import Empty
from multiprocessing import Queue
from typing import Dict, List, Any
import time

from crumb.settings import Settings
from crumb.logger import log, logging
from .generic import TaskToBeDone  # pylint: disable=unused-import


def do_work(tasks_to_be_done: "Queue[TaskToBeDone]", tasks_that_are_done: Queue, log_queue: Queue) -> bool:
    """
    Task for workers.
    This function goes through the list of tasks, executes and returns the result.
    """
    while True:
        task = tasks_to_be_done.get(True)  # block until there is data
        if (task['node'] is None) and task['input']['kill']:
            log(log_queue, 'worker> kill call', logging.INFO)
            break
        log(log_queue, 'worker> task is', logging.DEBUG)
        if hasattr(task['node'].bakery_item, 'func'):
            log(log_queue, f"worker> function is {task['node'].bakery_item.func}", logging.DEBUG)
        task['output'] = task['node'].run(task['input'])
        task['node'] = task['node'].name  # we dont need the node anymore
        # run and return results
        tasks_that_are_done.put(task)
    return True


def do_schedule(lock, tasks_to_be_done: "Queue[TaskToBeDone]", tasks_that_are_done: Queue, log_queue: Queue,
                results, input_for_nodes, deps_to_nodes, nodes_to_deps, node_waiting) -> bool:
    """
    Task for scheduler jobs.
    This function checks tasks that are done and compile finished dependencies for other nodes.
    """
    while True:
        log(log_queue, f'scheduler> there are still {len(node_waiting)} waiting', logging.INFO)
        log(log_queue, "scheduler status: ", logging.DEBUG, payload={'deps_to_nodes': deps_to_nodes, 'nodes_to_deps': nodes_to_deps})
        # get done task
        task = tasks_that_are_done.get(True)
        if (task['node'] is None) and task['input']['kill']:
            log(log_queue, 'scheduler> kill call', logging.INFO)
            break
        log(log_queue, f'scheduler> processing complete task: {task}', logging.INFO)
        # add output to the results
        results[task['node']] = task['output']
        # if they are in the dependencies of others
        if task['node'] in deps_to_nodes:
            # get these dependencies
            lock.acquire()
            for node_name in deps_to_nodes[task['node']]:
                # remove dependency for the task finished
                n2d = nodes_to_deps[node_name]
                n2d.remove(task['node'])
                nodes_to_deps[node_name] = n2d
                # if there are no more dependencies prepare it to run
                if len(nodes_to_deps[node_name]) == 0:
                    nodes_to_deps.pop(node_name)
                    # collect input for node
                    node = node_waiting[node_name]
                    # get all inputs - they are done
                    if node_name in input_for_nodes:
                        collected_inputs = input_for_nodes[node_name]
                    else:
                        collected_inputs = {}
                    for input_name, from_other_nodes in node.input.items():
                        if not from_other_nodes:
                            continue
                        (previous_node, other_node_input) = from_other_nodes
                        log(log_queue, "Scheduler computing input", logging.DEBUG, payload={'input_name': input_name, 'previous_node': previous_node, 'other_node_input': other_node_input})
                        collected_inputs[input_name] = results[previous_node.name][other_node_input]
                    input_for_nodes[node_name] = collected_inputs
                    # remove from waiting list
                    node_waiting.pop(node_name)
                    # send for execution
                    log(log_queue, 'scheduler> adding', logging.DEBUG, payload={'node': node, f'input_for_nodes[{node_name}]': input_for_nodes[node_name]})
                    tasks_to_be_done.put({'node': node, 'input': input_for_nodes[node_name]})
                    input_for_nodes.pop(node_name)  # we can clean this as it was already sent
                else:
                    log(log_queue, f'scheduler> there are still {len(nodes_to_deps[node_name])} dependencies for {node_name}', logging.DEBUG)
            # since task already run we can remove from dependencies
            deps_to_nodes.pop(task['node'])
            lock.release()
    log(log_queue, 'scheduler> is over', logging.INFO)
    return True


def wait_work(tasks_to_be_done: "Queue[TaskToBeDone]", log_queue: Queue, waiting_for: List[str], results: Dict[str, Dict[str, Any]]) -> bool:
    """
    Function for Process MultiSlicer-Wait to loop and wait while there are tasks to be executed
    """
    while True:
        # check if we have all that we need
        log(log_queue, f"wait> we have:, {sum(i in results for i in waiting_for)} out of {len(waiting_for)}", logging.DEBUG)
        if all(i in results for i in waiting_for):
            log(log_queue, 'wait> we are done!', logging.INFO)
            break
        # check if we should stop work in the middle
        try:
            task_check = tasks_to_be_done.get_nowait()
        except Empty:
            pass
        else:
            if (task_check['node'] is None) and task_check['input']['kill']:
                log(log_queue, 'wait> kill call', logging.INFO)
                break
            # if it is not the kill call place it back
            tasks_to_be_done.put(task_check)
        time.sleep(Settings.MULTISLICER_WAITWORKER_DELAY)
    log(log_queue, 'tasks are done', logging.INFO)
    return True
