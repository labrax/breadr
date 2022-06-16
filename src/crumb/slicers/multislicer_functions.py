"""Functions for multislicer processes"""
from queue import Empty
from multiprocessing import Queue
from typing import Dict, List, Any
import time
import crumb.settings
from .generic import TaskToBeDone  # pylint: disable=unused-import


def do_work(tasks_to_be_done: "Queue[TaskToBeDone]", tasks_that_are_done: Queue) -> bool:
    """
    Task for workers.
    This function goes through the list of tasks, executes and returns the result.
    """
    while True:
        task = tasks_to_be_done.get(True)  # block until there is data
        if (task['node'] is None) and task['input']['kill']:
            if crumb.settings.DEBUG_VERBOSE:
                print('worker> kill call')
            break
        if crumb.settings.DEBUG_VERBOSE:
            print('worker> task is', task)
            if hasattr(task['node'].bakery_item, 'func'):
                print('worker> function is', task['node'].bakery_item.func)
        task['output'] = task['node'].run(task['input'])
        task['node'] = task['node'].name  # we dont need the node anymore
        # run and return results
        tasks_that_are_done.put(task)
    return True


def do_schedule(lock, tasks_to_be_done: "Queue[TaskToBeDone]", tasks_that_are_done: Queue, results, input_for_nodes, deps_to_nodes, nodes_to_deps, node_waiting) -> bool:
    """
    Task for scheduler jobs.
    This function checks tasks that are done and compile finished dependencies for other nodes.
    """
    while True:
        if crumb.settings.DEBUG_VERBOSE:
            print('scheduler> loop')
        # compile tasks that are done
        if crumb.settings.DEBUG_VERBOSE:
            print(f'scheduler> there are still {len(node_waiting)} waiting')
            print('scheduler>', deps_to_nodes)
            print('scheduler>', nodes_to_deps)
            for node_pending, all_their_dependency in nodes_to_deps.items():
                print('scheduler> pending', node_pending)
                for their_dependency in all_their_dependency:
                    print(node_pending in results, their_dependency in results)
                    if their_dependency in results:
                        print(results[their_dependency])
        # get done task
        task = tasks_that_are_done.get(True)
        if (task['node'] is None) and task['input']['kill']:
            if crumb.settings.DEBUG_VERBOSE:
                print('scheduler> kill call')
            break

        if crumb.settings.DEBUG_VERBOSE:
            print('scheduler> processing complete task:', task)
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
                        if crumb.settings.DEBUG_VERBOSE:
                            print('scheduler>', input_name, previous_node, other_node_input)
                        collected_inputs[input_name] = results[previous_node.name][other_node_input]
                    input_for_nodes[node_name] = collected_inputs
                    # remove from waiting list
                    node_waiting.pop(node_name)
                    # send for execution
                    if crumb.settings.DEBUG_VERBOSE:
                        print('scheduler> adding', node, input_for_nodes[node_name])
                    tasks_to_be_done.put({'node': node, 'input': input_for_nodes[node_name]})
                    input_for_nodes.pop(node_name)  # we can clean this as it was already sent
                else:
                    if crumb.settings.DEBUG_VERBOSE:
                        print(f'scheduler> there are still {len(nodes_to_deps[node_name])} dependencies for {node_name}')
            # since task already run we can remove from dependencies
            deps_to_nodes.pop(task['node'])
            lock.release()
    if crumb.settings.DEBUG_VERBOSE:
        print('scheduler> is over')
    return True


def wait_work(tasks_to_be_done: "Queue[TaskToBeDone]", waiting_for: List[str], results: Dict[str, Dict[str, Any]]) -> bool:
    """
    Function for Process MultiSlicer-Wait to loop and wait while there are tasks to be executed
    """
    while True:
        # check if we have all that we need
        if crumb.settings.DEBUG_VERBOSE:
            print('wait> we have:', sum(i in results for i in waiting_for), 'out of', len(waiting_for))
        if all(i in results for i in waiting_for):
            if crumb.settings.DEBUG_VERBOSE:
                print('wait> we are done!')
            break
        # check if we should stop work in the middle
        try:
            task_check = tasks_to_be_done.get_nowait()
        except Empty:
            pass
        else:
            if (task_check['node'] is None) and task_check['input']['kill']:
                if crumb.settings.DEBUG_VERBOSE:
                    print('wait> kill call')
                break
            # if it is not the kill call place it back
            tasks_to_be_done.put(task_check)
        time.sleep(crumb.settings.MULTISLICER_WAITWORKER_DELAY)
    if crumb.settings.DEBUG_VERBOSE:
        print('tasks are done')
    return True
