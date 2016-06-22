import platform
import os

COMMAND_GIT = "git"
COMMAND_HG = "hg"
COMMAND_SVN = "svn"
COMMAND_PYTHON = "python"
COMMAND_PATCH = "patch"


def _find_command(command, paths_to_search):
    command_res = command

    for path in paths_to_search:
        command_abs = os.path.join(path, command)
        if os.path.exists(command_abs):
            command_res = command_abs
            break

    return command_res


def initialize_commands():
    global COMMAND_GIT
    global COMMAND_HG
    global COMMAND_SVN
    global COMMAND_PYTHON
    global COMMAND_PATCH

    if platform.system() is not "Windows":
        # we search in the PATH as well as in some obvious locations
        paths_to_search = os.environ["PATH"].split(":") + ["/usr/local/bin", "/opt/local/bin", "/usr/bin"]
        COMMAND_GIT = _find_command(COMMAND_GIT, paths_to_search)
        COMMAND_HG = _find_command(COMMAND_HG, paths_to_search)
        COMMAND_SVN = _find_command(COMMAND_SVN, paths_to_search)
        COMMAND_PYTHON = _find_command(COMMAND_PYTHON, paths_to_search)
        COMMAND_PATCH = _find_command(COMMAND_PATCH, paths_to_search)


def command_git():
    return COMMAND_GIT


def command_hg():
    return COMMAND_HG


def command_svn():
    return COMMAND_SVN


def command_python():
    return COMMAND_PYTHON


def command_patch():
    return COMMAND_PATCH
