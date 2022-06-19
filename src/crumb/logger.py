"""Define structure to obtain status and logs"""
import atexit
import multiprocessing
from multiprocessing import Queue, Process
import logging
from typing import Optional

from crumb.settings import Settings


def log(logger_queue: Queue, message: str, log_level: int, payload: dict = None):
    """Adds a message to the logging queue"""
    logger_queue.put({'process': multiprocessing.current_process().name, 'message': message, 'logging_level': log_level, 'payload': str(payload)})


def do_log_task(logger_queue: Queue):
    """Task for logger"""
    logging.basicConfig(level=Settings.LOGGING_LEVEL, filename=Settings.LOGGING_FILENAME, format=Settings.LOGGING_FORMAT)
    logger = logging.getLogger()

    while True:
        lmsg = logger_queue.get(True)
        if lmsg['message'] is None:
            break
        logger.log(lmsg['logging_level'], "[%s]: %s", lmsg['process'], lmsg['message'])
        if lmsg['payload'] != 'None':
            logger.log(lmsg['logging_level'], lmsg['payload'])
    return True


class LoggerQueue:
    """Stores the queue for the logger"""
    LOGGER_QUEUE: Optional[Queue] = None
    process: Optional[Process] = None

    @classmethod
    def get_logger(cls) -> Queue:
        """Get the Queue"""
        if cls.LOGGER_QUEUE is None:
            cls.LOGGER_QUEUE = Queue()
            if multiprocessing.current_process().name == 'MainProcess':
                cls.start_task()
        return cls.LOGGER_QUEUE

    @classmethod
    def start_task(cls) -> None:
        """Starts the logger task"""
        if cls.process is not None:
            raise RuntimeError('Logger task is already running.')
        cls.process = Process(target=do_log_task,
                              name='Logger-Wait',
                              args=(cls.get_logger(), ))
        cls.process.start()
        atexit.register(cls.kill)

    @classmethod
    def kill(cls) -> None:
        """Stops the logger class"""
        if cls.process is None:
            raise RuntimeError('Logger task is already done.')
        if cls.LOGGER_QUEUE is None:  # this error should never happen!
            raise RuntimeError('Queue does not exist?')
        cls.LOGGER_QUEUE.put({'message': None})
        cls.process.join()
        cls.process = None
