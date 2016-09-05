from __future__ import print_function

VERBOSITY = 0


def set_verbosity(verbosity):
    global VERBOSITY
    VERBOSITY = 0 if verbosity == None else verbosity

def verbosity():
    return VERBOSITY


def log(message):
    print(message)


def log_verbose(message, level=1):
    if VERBOSITY >= level:
        print("--- " + message)


def log_warning(message):
    print("--- WARNING: " + message)


def log_error(message):
    print("--- ERROR: " + message)
