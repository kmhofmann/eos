from __future__ import print_function

VERBOSITY = 0


def set_verbosity(verbosity):
    global VERBOSITY
    VERBOSITY = verbosity


def verbosity():
    global VERBOSITY
    return VERBOSITY


def log(message):
    print(message)


def log_verbose(message, level=1):
    global VERBOSITY
    if VERBOSITY >= level:
        print("--- " + message)


def log_warning(message):
    print("--- WARNING: " + message)


def log_error(message):
    print("--- ERROR: " + message)
