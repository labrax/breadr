"""Global settings for the execution"""

from typing import Any
import logging


class Settings:
    """Settings store"""
    # logging settings
    LOGGING_LEVEL = logging.WARNING
    LOGGING_FILENAME = None
    LOGGING_FORMAT = '%(asctime)s %(levelname)s %(message)s'
    # ensure that warnings come twice for tests
    LOGGING_WARNING_TWICE = False
    # if started as single, then exec as multi, then changed to single it might break depending where the functions come from!
    # if the functions come from top level of a file it will work
    USE_MULTISLICER = False
    MULTISLICER_WAITWORKER_DELAY = .1  # TODO: this setting might not work
    MULTISLICER_THREADS = 4
    # if atexit does not work properly it will be required to manually ask the threads to exit!
    MULTISLICER_START_THEN_KILL_THREADS = False

    @classmethod
    def set_setting(cls, setting: str, new_value: Any) -> None:
        """Set a setting into a new value if valid"""
        if hasattr(cls, setting):
            if isinstance(getattr(cls, setting), type(new_value)):
                setattr(cls, setting, new_value)
            else:
                raise TypeError(f'Invalid value for setting "{setting}", got "{type(new_value)}" expected "{type(getattr(cls, setting))}"')
        else:
            raise AttributeError(f'Setting {setting} not found.')
