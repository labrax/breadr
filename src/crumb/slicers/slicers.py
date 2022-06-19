"""
Module Slicers
Obtain and delete the current Slicer executor
"""

from crumb.settings import Settings
from crumb.slicers.generic import Slicer
from crumb.slicers.multislicer import MultiSlicer
from crumb.slicers.singleslicer import SingleSlicer


def get_slicer():
    """
    Returns the executor for the nodes.
    Depending on the settings, this could either be multi or single process.
    """
    if Slicer.TASK_EXECUTOR_INSTANCE is None:
        if Settings.USE_MULTISLICER:
            # inside there is another singleton
            Slicer.TASK_EXECUTOR_INSTANCE = MultiSlicer()
        else:
            # inside there is another singleton
            Slicer.TASK_EXECUTOR_INSTANCE = SingleSlicer()
    return Slicer.TASK_EXECUTOR_INSTANCE


def delete_slicer():
    """
    Deletes the current slicer.
    This can be used to reset the slicer and start with another one (after changing settings)
    """
    if Slicer.TASK_EXECUTOR_INSTANCE:
        Slicer.TASK_EXECUTOR_INSTANCE.kill()
    Slicer.TASK_EXECUTOR_INSTANCE = None
