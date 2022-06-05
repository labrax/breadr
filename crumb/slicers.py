
import crumb.settings

from multiprocessing import Manager, Lock, Process, Queue
from queue import Empty
import time

def do_work(tasks_to_be_done, tasks_that_are_done):
    while True:
        try:
            task = tasks_to_be_done.get_nowait()
        except Empty:
            if crumb.settings.debug:
                print('worker> no task to be done')
            time.sleep(crumb.settings.multislicer_worker_delay)
        else:
            if (task['node'] is None) and task['input']['kill']:
                if crumb.settings.debug:
                    print('worker> kill call')
                break
            if crumb.settings.debug:
                print('worker> task is', task)
                print('worker> function is', task['node'].bakery_item.func)
            task['output'] = task['node'].run(task['input'])
            task['node'] = task['node'].name # we dont need the node anymore
            # run and return results
            tasks_that_are_done.put(task)
    return True

def do_schedule(lock, tasks_to_be_done, tasks_that_are_done, results, input_for_nodes, deps_to_nodes, nodes_to_deps, node_waiting):
    while True:
        if crumb.settings.debug:
            print('scheduler> loop')
        lock.acquire()
        # compile tasks that are done
        try:
            if crumb.settings.debug:
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
            task = tasks_that_are_done.get_nowait()
        except Empty:
            pass
        else:
            if crumb.settings.debug:
                print('scheduler> processing complete task:', task)
            # add output to the results
            results[task['node']] = task['output']
            # if they are in the dependencies of others
            if task['node'] in deps_to_nodes:
                # get these dependencies
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
                        d = {}
                        for input_name, (previous_node, other_node_input) in node.input.items():
                            print(input_name, previous_node, other_node_input)
                            d[input_name] = results[previous_node.name][other_node_input]
                        input_for_nodes[node_name] = d
                        # remove from waiting list
                        node_waiting.pop(node_name)
                        # send for execution
                        if crumb.settings.debug:
                            print('scheduler> adding', node, input_for_nodes[node_name])
                        tasks_to_be_done.put({'node': node, 'input': input_for_nodes[node_name]})
                        input_for_nodes.pop(node_name) # we can clean this as it was already sent
                    else:
                        if crumb.settings.debug:
                            print(f'scheduler> there are still {len(nodes_to_deps[node_name])} dependencies for {node_name}')
                # since task already run we can remove from dependencies
                deps_to_nodes.pop(task['node'])
        finally:
            lock.release()
            time.sleep(crumb.settings.multislicer_scheduler_delay)
        
        # check if we should close
        try:
            if crumb.settings.debug:
                print('scheduler> checking kill call')
            task = tasks_to_be_done.get_nowait()
        except Empty:
            pass
        else:
            if (task['node'] is None) and task['input']['kill']:
                if crumb.settings.debug:
                    print('scheduler> kill call')
                break
            else:
                tasks_to_be_done.put(task)
    if crumb.settings.debug:
        print('scheduler> is over')
    return True

def wait_work(tasks_to_be_done, waiting_for, results):
    while True:
        # check if we have all that we need
        if crumb.settings.debug:
            print('wait> we have:', sum([i in results for i in waiting_for]), 'out of', len(waiting_for))
        if all([i in results for i in waiting_for]):
            break
        # check if we should stop work in the middle
        try:
            task_check = tasks_to_be_done.get_nowait()
        except Empty:
            pass
        else:
            if (task_check['node'] is None) and task_check['input']['kill']:
                if crumb.settings.debug:
                    print('wait> kill call')
                break
            else: # if it is not the kill call place it back
                tasks_to_be_done.put(task_check)
        time.sleep(crumb.settings.multislicer_wait_worker_delay)
    if crumb.settings.debug:
        print('tasks are done')
    return True

class MultiSlicer:
    def __new__(cls):
        global task_executor_instance
        try: task_executor_instance
        except NameError:
            task_executor_instance = super().__new__(cls)
            task_executor_instance.reset()
        return task_executor_instance

    def kill(self):
        if hasattr(self, 'processes'):
            # if task executor was started before lets kill everything then restart
            while not self.tasks_to_be_done.empty():
                self.tasks_to_be_done.get()
            for _ in range(len(self.processes)):
                self.tasks_to_be_done.put({'node': None, 'input': {'kill': True}})
            if crumb.settings.debug:
                print(f'{self.__class__.__name__} waiting for all processes to join')
            for i in self.processes:
                if crumb.settings.debug:
                    print('slicer> joining', i)
                i.join()

    def reset(self, number_processes=crumb.settings.multislicer_threads):
        self.kill()

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

        # need to remove the functions to prepare for running
        for el in task_seq:
            node = el['node']
            node.bakery_item.prepare_for_exec()

        try:
            # if some nodes require some input add them to the relation first
            if not inputs_required is None:
                for (node_name, node_input), value in inputs_required.items():
                    if not node_name in self.input_for_nodes:
                        self.input_for_nodes[node_name] = {node_input: value}
                    else:
                        # need to reassign due to the way objects in multiprocessing work
                        d = self.input_for_nodes[node_name]
                        d[node_input] = value
                        self.input_for_nodes[node_name] = d

            # compute nodes with node-node dependencies
            for el in task_seq:
                node, deps = el['node'], el['deps']
                if len(deps) == 0:
                    if not node.name in self.input_for_nodes:
                        self.tasks_to_be_done.put({'node': node, 'input': {}})
                    else:
                        self.tasks_to_be_done.put({'node': node, 'input': self.input_for_nodes[node.name]})
                    continue
                self.node_waiting[node.name] = node
                self.nodes_to_deps[node.name] = deps
                for d in deps:
                    if not d in self.deps_to_nodes:
                        self.deps_to_nodes[d] = [node.name]
                    else:
                        # it is silly, but this is the way to share objects using multiprocessing
                        l = self.deps_to_nodes[d]
                        l.append(node.name)
                        self.deps_to_nodes[d] = l
        finally:
            if crumb.settings.debug:
                print('add task> finished giving tasks')
            self.lock.release()

        p = Process(target=wait_work, args=(self.tasks_to_be_done, [i['node'].name for i in task_seq], self.results))
        # self.processes.append(p)
        p.start()
        p.join()
        
        to_ret = dict()
        for i in task_seq:
            to_ret[i['node'].name] = self.results[i['node'].name]
            self.results.pop(i['node'].name) # results are not needed here
        return to_ret
