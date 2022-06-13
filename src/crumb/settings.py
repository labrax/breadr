"""Global settings for the execution"""

DEBUG_VERBOSE = False
# if started as single, then exec as multi, then changed to single it might break depending where the functions come from!
# if the functions come from top level of a file it will work
USE_MULTISLICER = False
MULTISLICER_WAITWORKER_DELAY = .5
MULTISLICER_THREADS = 4
# if atexit does not work properly it will be required to manually ask the threads to exit!
MULTISLICER_START_THEN_KILL_THREADS = False
