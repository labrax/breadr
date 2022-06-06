
import crumb.settings
from crumb.slicers.multislicer import MultiSlicer
from crumb.slicers.singleslicer import SingleSlicer

def get_slicer():
    """
    Returns the executor for the nodes.
    Depending on the settings, this could either be multi or single process.
    """
    global task_executor_instance
    try: task_executor_instance
    except NameError:
        if crumb.settings.multislicer:
            task_executor_instance = MultiSlicer() # inside there is another singleton
        else:
            task_executor_instance = SingleSlicer() # inside there is another singleton
    return task_executor_instance

def delete_slicer():
    """
    Deletes the current slicer.
    This can be used to reset the slicer and start with another one (after changing settings)
    """
    global task_executor_instance
    try: 
        del task_executor_instance
    except NameError:
        pass
