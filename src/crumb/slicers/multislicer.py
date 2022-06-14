"""Executor with multiprocessing support"""
from multiprocessing import Manager, Lock, Process, Queue
from queue import Empty
import atexit
from typing import Dict, List, Tuple, Any, Union

import crumb.settings
from crumb.node import Node
from .multislicer_functions import do_schedule, do_work, wait_work
from .generic import Slicer, TaskDependencies, TaskToBeDone


class MultiSlicer(Slicer):
    """
    Multiprocessing executor
    """
    TASK_EXECUTOR_INSTANCE = None

    def __new__(cls):
        if cls.TASK_EXECUTOR_INSTANCE is None:
            cls.TASK_EXECUTOR_INSTANCE = super().__new__(cls)
            cls.TASK_EXECUTOR_INSTANCE.reset()
        return cls.TASK_EXECUTOR_INSTANCE

    def kill(self) -> None:
        """Kill all the multiprocessing processes"""
        if crumb.settings.DEBUG_VERBOSE:
            print('multislicer> starting kill ritual')
        if hasattr(self, 'processes'):
            # if task executor was started before lets kill everything then restart
            while not self.tasks_to_be_done.empty():
                try:
                    self.tasks_to_be_done.get()
                except Empty:
                    pass
            self.tasks_done.put({'node': None, 'input': {'kill': True}})  # one for the scheduler
            for _ in range(len(self.processes)):
                self.tasks_to_be_done.put({'node': None, 'input': {'kill': True}})  # other for workers/wait
            if crumb.settings.DEBUG_VERBOSE:
                print(f'{self.__class__.__name__} waiting for all processes to join')
            for i in self.processes:
                if crumb.settings.DEBUG_VERBOSE:
                    print('slicer> joining', i)
                i.join()
            del self.processes

    def reset(self, number_processes: int = crumb.settings.MULTISLICER_THREADS) -> None:
        """
        @param number_processes: restarts the MultiSlicer with a number of work processes
        """
        self.kill()
        if not hasattr(self, 'processes'):
            atexit.register(self.kill)  # this is because __del__ is too late!
        self.manager = Manager()
        self.lock = Lock()
        self.n_jobs = self.manager.Value(int, 0)
        self.processes: List[Process] = []
        self.number_processes = number_processes
        # ready for execution
        # [{'node': node, 'input': {name': value}}]
        self.tasks_to_be_done: "Queue[TaskToBeDone]" = Queue()
        # ready to be transmitted to results
        # {'node_name': node, 'output': {'name': value}}
        self.tasks_done: Queue = Queue()
        # {node_name: {var: value}}
        self.results: Dict[str, Any] = self.manager.dict()
        # {node_name: {var: value}}
        self.input_for_nodes: Dict[str, Dict[str, Any]] = self.manager.dict()
        # {node_name: node}
        self.node_waiting: Dict[str, Node] = self.manager.dict()
        # {deps: [node_name]}
        self.deps_to_nodes: Dict[str, List[Node]] = self.manager.dict()
        # if node not in here it means dependencies were solved and sent for execution
        # {node_name: [deps]}
        self.nodes_to_deps: Dict[str, List[str]] = self.manager.dict()
        scheduler_process = Process(target=do_schedule,
                                    name='MultiSlicer-Scheduler',
                                    args=(self.lock,
                                          self.tasks_to_be_done, self.tasks_done,
                                          self.results, self.input_for_nodes,
                                          self.deps_to_nodes, self.nodes_to_deps, self.node_waiting))
        self.processes.append(scheduler_process)
        scheduler_process.start()
        for i in range(self.number_processes):
            worker_process = Process(target=do_work,
                                     name=f'MultiSlicer-Worker-{i}',
                                     args=(self.tasks_to_be_done, self.tasks_done))
            self.processes.append(worker_process)
            worker_process.start()

    def start_if_needed(self) -> None:
        """Start the threads if they are not running"""
        if not hasattr(self, 'processes'):
            self.reset()

    def add_work(self, task_seq: List[TaskDependencies], inputs_required: Dict[Tuple[str, str], Any] = None) -> Union[Dict[str, Any], Any]:
        self.start_if_needed()
        self.lock.acquire()
        self.n_jobs.value += 1

        # need to remove the functions to prepare for running
        # this is because multiprocessing might not be able to find the function (e.g. on Windows)
        def _prepare_node_for_exec(node):
            if node.bakery_item.__class__.__name__ == 'Crumb':
                node.bakery_item.func = None
            elif node.bakery_item.__class__.__name__ == 'Slice':
                for sub_node in node.bakery_item.values():
                    _prepare_node_for_exec(sub_node['node'])
            else:
                raise NotImplementedError('bakery item inside node not known')
        for task_element in task_seq:
            _prepare_node_for_exec(task_element['node'])

        try:
            # if some nodes require some input add them to the relation first
            if inputs_required is not None:
                for (node_name, node_input), value in inputs_required.items():
                    if node_name not in self.input_for_nodes:
                        self.input_for_nodes[node_name] = {node_input: value}
                    else:
                        # need to reassign due to the way objects in multiprocessing work
                        temp_dict = self.input_for_nodes[node_name]
                        temp_dict[node_input] = value
                        self.input_for_nodes[node_name] = temp_dict

            # compute nodes with node-node dependencies
            for task_element in task_seq:
                node, deps = task_element['node'], task_element['deps']
                if len(deps) == 0:
                    if node.name not in self.input_for_nodes:
                        self.tasks_to_be_done.put({'node': node, 'input': {}})
                    else:
                        self.tasks_to_be_done.put({'node': node, 'input': self.input_for_nodes[node.name]})
                    continue
                self.node_waiting[node.name] = node
                self.nodes_to_deps[node.name] = deps
                for dependency in deps:
                    if dependency not in self.deps_to_nodes:
                        self.deps_to_nodes[dependency] = [node.name]
                    else:
                        # it is silly, but this is the way to share objects using multiprocessing
                        temp_list = self.deps_to_nodes[dependency]
                        temp_list.append(node.name)
                        self.deps_to_nodes[dependency] = temp_list
        finally:
            if crumb.settings.DEBUG_VERBOSE:
                print('add task> finished giving tasks')
            self.lock.release()
        waitwork_process = Process(target=wait_work,
                                   name='MultiSlicer-Wait',
                                   args=(self.tasks_to_be_done, [i['node'].name for i in task_seq], self.results))
        self.processes.append(waitwork_process)
        waitwork_process.start()
        waitwork_process.join()
        self.processes.remove(waitwork_process)
        self.lock.acquire()
        self.n_jobs.value -= 1
        self.lock.release()
        if self.n_jobs.value == 0 and crumb.settings.MULTISLICER_START_THEN_KILL_THREADS:
            if crumb.settings.DEBUG_VERBOSE:
                print('add task > kill trigger')
            self.kill()
        # prepare data for return
        to_ret = {}
        for i in task_seq:
            # this is needed for MultiSlicer
            if i['node'].save_exec:
                i['node'].last_exec = self.results[i['node'].name]
            to_ret[i['node'].name] = self.results[i['node'].name]
            self.results.pop(i['node'].name)  # results are not needed here
        return to_ret
