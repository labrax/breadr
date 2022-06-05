
import crumb.settings
from crumb.slicers.multislicer import MultiSlicer
from crumb.slicers.singleslicer import SingleSlicer

def get_slicer():
    global task_executor_instance
    try: task_executor_instance
    except NameError:
        if crumb.settings.multislicer:
            task_executor_instance = MultiSlicer() # inside there is another singleton
        else:
            task_executor_instance = SingleSlicer() # inside there is another singleton
    return task_executor_instance
