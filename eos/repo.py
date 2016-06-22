import os
import shutil
import eos.log
import eos.util

# TODO: more robust tool detection
COMMAND_HG = "hg"
COMMAND_GIT = "git"
COMMAND_SVN = "svn"


def check_return_code(code):
    if code != 0:
        raise RuntimeError("repository operation failed")


def remove_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)


def hg_repo_exists(dir):
    # TODO: more robust check
    return os.path.exists(os.path.join(dir, ".hg"))


def git_repo_exists(dir):
    # TODO: more robust check
    return os.path.exists(os.path.join(dir, ".git"))


def hg_clone(url, directory):
    return eos.util.execute_command(COMMAND_HG + " clone " + url + " " + directory)


def hg_pull(directory):
    return eos.util.execute_command(COMMAND_HG + " pull -R " + directory)


def hg_set_to_revision(directory, revision=None):
    if revision is None:
        revision = ""
    status = eos.util.execute_command(COMMAND_HG + " update -R " + directory + " -C " + revision)
    if not status:
        return False
    return eos.util.execute_command(COMMAND_HG + " purge -R " + directory + " --config extensions.purge=")


def git_clone(url, directory):
    return eos.util.execute_command(COMMAND_GIT + " clone --recursive " + url + " " + directory)


def git_fetch(directory):
    return eos.util.execute_command(COMMAND_GIT + " -C " + directory + " fetch --recurse-submodules")


def git_set_to_revision(directory, revision=None):
    if revision is None:
        revision = "HEAD"
    status = eos.util.execute_command(COMMAND_GIT + " -C " + directory + " reset --hard " + revision)
    if not status:
        return False
    return eos.util.execute_command(COMMAND_GIT + " -C " + directory + " clean -fxd")


def svn_checkout(url, directory):
    return eos.util.execute_command(COMMAND_SVN + " checkout " + url + " " + directory)


def update_state(repo_type, url, name, dst_dir, revision=None):
    eos.log("Updating repository for '" + name + "' (url = " + url + ", target_dir = " + dst_dir + ")")

    try:
        if repo_type == "git":
            if git_repo_exists(dst_dir):
                check_return_code(git_fetch(dst_dir))
            else:
                remove_directory(dst_dir)
                check_return_code(git_clone(url, dst_dir))

            check_return_code(git_set_to_revision(dst_dir, revision))
        elif repo_type == "hg":
            if hg_repo_exists(dst_dir):
                check_return_code(hg_pull(dst_dir))
            else:
                remove_directory(dst_dir)
                check_return_code(hg_clone(url, dst_dir))

            check_return_code(hg_set_to_revision(dst_dir, revision))
        elif repo_type == "svn":
            remove_directory(dst_dir)
            check_return_code(svn_checkout(url, dst_dir))
            if revision and revision != "":
                eos.log_error("cannot update SVN repository to revision")
                return False
        else:
            eos.log_error("unknown repository type '" + repo_type + "'")
            return False
    except RuntimeError:
        return False

    return True
