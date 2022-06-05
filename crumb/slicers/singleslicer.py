
from .base import Slicer

class SingleSlicer(Slicer):
    """
    Executes the slices with a single-process approach.
    This is useful when there are not many operations, or a few heavy ones.
    The functions are not reloaded, and can be created from inside classes, or other functions.
    """
    def __new__(cls):
        global task_executor_instance
        try: task_executor_instance
        except NameError:
            task_executor_instance = super().__new__(cls)
            task_executor_instance.reset()
        return task_executor_instance

    def reset(self):
        self.kill()
        # ready for execution
        self.tasks_to_be_done = list() # [{'node': node, 'input': {name': value}}]

        self.results = dict() # {node_name: {var: value}}
        self.input_for_nodes = dict() # {node_name: {var: value}}

        self.node_waiting = dict() # {node_name: node}
        self.deps_to_nodes = dict() # {deps: [node_name]}
        # if node not in here it means dependencies were solved and executed
        self.nodes_to_deps = dict() # {node_name: [deps]}

    def _exec(self):
        ## TODO: implement
        pass

    def add_work(self, task_seq, inputs_required=None):
        """
        Add tasks that need to be executed
        @param task_seq: format is: {'node': node_id, 'deps': [node_id_1, node_id_2, ...]}
        @param inputs_required: format is {(node_name, node_input): value}
        """
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
                    self.tasks_to_be_done.append({'node': node, 'input': {}})
                else:
                    self.tasks_to_be_done.append({'node': node, 'input': self.input_for_nodes[node.name]})
                continue
            self.node_waiting[node.name] = node
            self.nodes_to_deps[node.name] = deps
            for d in deps:
                if not d in self.deps_to_nodes:
                    self.deps_to_nodes[d] = list()
                self.deps_to_nodes[d].append(node.name)

        self._exec()
        
        to_ret = dict()
        for i in task_seq:
            to_ret[i['node'].name] = self.results[i['node'].name]
            self.results.pop(i['node'].name) # results are not needed here
        return to_ret
