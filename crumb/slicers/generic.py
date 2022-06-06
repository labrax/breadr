

class Slicer:
    """
    Virtual definition for graph executors
    """
    def reset(*args, **kwargs):
        """
        Reset the executor. Stops the queue and cancel jobs
        """
        raise NotImplementedError()

    def add_work(self, task_seq, inputs_required=None, *args, **kwargs):
        """
        Add tasks that need to be executed
        @param task_seq: format is: {'node': node_id, 'deps': [node_id_1, node_id_2, ...]}
        @param inputs_required: format is {(node_name, node_input): value}
        """
        raise NotImplementedError()