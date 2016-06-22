from __future__ import print_function

VERBOSE = False


def set_verbose(verbose):
    global VERBOSE
    VERBOSE = verbose


def is_verbose():
    return VERBOSE


def log(message):
    print("--- " + message)


def log_verbose(message):
    if VERBOSE:
        print("=== " + message)


def log_warning(message):
    print("WARNING: " + message)


def log_error(message):
    print("ERROR: " + message)
