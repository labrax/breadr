
from multiprocessing import Manager, Lock, Process, Queue
from queue import Empty
import time

def do_work(tasks_to_be_done, tasks_that_are_done):
    while True:
        try:
            task = tasks_to_be_done.get_nowait()
        except Empty:
            time.sleep(1)
        else:
            if (task['node'] is None) and task['input']['kill']:
                break
            task['node'] = task['node'].name
            task['output'] = task['node'].run(task['input'])
            # run and return results
            tasks_that_are_done.put(task)

def do_schedule(lock, tasks_to_be_done, tasks_that_are_done, results, input_for_nodes, deps_to_nodes, nodes_to_deps, node_waiting):
    while True:
        lock.acquire()
        # check if we should close
        task_check = tasks_to_be_done.get()
        if (task_check['node'] is None) and task_check['input']['kill']:
            break
        # 
        # compile tasks that are done
        while not tasks_that_are_done.Empty:
            # get done task
            task = tasks_that_are_done.get()
            # add output to the results
            results[task['node']] = task['output']
            # if they are in the dependencies of others
            if task['node'] in deps_to_nodes:
                # get these dependencies
                for _, node_name in deps_to_nodes[task['node']]:
                    # remove dependency for the task finished
                    nodes_to_deps[node_name].remove(task['node'])
                    # if there are no more dependencies prepare it to run
                    if len(nodes_to_deps[node_name]) == 0:
                        nodes_to_deps.pop(node_name)
                        # collect input for node
                        node = node_waiting[node_name]
                        for input_name, (previous_node, other_node_input) in node.input.items():
                            if node_name not in input_for_nodes:
                                input_for_nodes[node_name] = dict()
                            input_for_nodes[node_name][input_name] = results[previous_node.name][other_node_input]
                        # remove from waiting list
                        node_waiting.pop(node_name)
                        # send for execution
                        tasks_to_be_done.put({'node': node, 'input': input_for_nodes[node_name]})
                # since task already run we can remove from dependencies
                deps_to_nodes.pop(task['node'])
        lock.release()
        time.sleep(1)

def wait_work(tasks_to_be_done, waiting_for, results):
    while True:
        if all([i in results for i in waiting_for]):
            break
        # check if we should stop work in the middle
        task_check = tasks_to_be_done.get()
        if (task_check['node'] is None) and task_check['input']['kill']:
            break
        time.sleep(1)

class TaskExecutor:
    def __new__(cls):
        global task_executor_instance
        try: task_executor_instance
        except NameError:
            task_executor_instance = super().__new__(cls)
            task_executor_instance.reset()
        return task_executor_instance

    def reset(self, number_processes=4):
        if hasattr(self, 'processes'):
            # if task executor was started before lets kill everything then restart
            while not self.tasks_to_be_done.empty():
                self.tasks_to_be_done.get()
            for _ in range(len(self.processes)):
                self.tasks_to_be_done.put({'node': None, 'input': {'kill': True}})
            print('Waiting for all processes to join')
            for i in self.processes:
                i.join()

        self.manager = Manager()
        self.lock = Lock()

        self.processes = list()
        self.number_processes = number_processes
        # ready for execution
        self.tasks_to_be_done = Queue() # [{'node': node, 'input': {name': value}}]
        # ready to be transmitted to results
        self.tasks_done = Queue() # {'node_name': node, 'output': {'name': value}}

        self.results = self.manager.dict() # {node_name: {var: value}}
        self.input_for_nodes = self.manager.dict() # {node_name: {var: value}}

        self.node_waiting = self.manager.dict() # {node_name: node}
        self.deps_to_nodes = self.manager.dict() # {deps: [node_name]}
        # if node not in here it means dependencies were solved and sent for execution
        self.nodes_to_deps = self.manager.dict() # {node_name: [deps]}

        p = Process(target=do_schedule, 
                    args=(self.lock, 
                        self.tasks_to_be_done, self.tasks_done, 
                        self.results, self.input_for_nodes,
                        self.deps_to_nodes, self.nodes_to_deps, self.node_waiting))
        self.processes.append(p)
        p.start()
        for _ in range(self.number_processes):
            p = Process(target=do_work, 
                        args=(self.tasks_to_be_done, self.tasks_done))
            self.processes.append(p)
            p.start()

    def add_work(self, task_seq, inputs_required=None):
        """
        Add tasks that need to be executed
        @param task_seq: format is: {'node': node_id, 'deps': [node_id_1, node_id_2, ...]}
        @param inputs_required: format is {(node_name, node_input): value}
        """
        self.lock.acquire()
        try:
            for el in task_seq:
                node, deps = el['node'], el['deps']
                if len(deps) == 0:
                    self.tasks_to_be_done.put({'node': node, 'input': {}})
                    break
                self.node_waiting[node.name] = node
                self.nodes_to_deps[node.name] = deps
                for d in deps:
                    if not d in self.deps_to_nodes:
                        self.deps_to_nodes[d] = list()
                    self.deps_to_nodes[d].append(node.name)
            if inputs_required:
                for (node_name, node_input), value in inputs_required.items():
                    if node_name not in self.input_for_nodes:
                        self.input_for_nodes[node.name] = dict()
                    self.input_for_nodes[node.name][node_input] = value
        finally:
            self.lock.release()
        p = Process(target=wait_work, args=(self.tasks_to_be_done, [i['node'].name for i in task_seq], self.results))
        self.processes.append(p)
        p.start()
        p.join() #TODO: this will lock everything?
