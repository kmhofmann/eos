import os
import shutil
import eos.log
import eos.util

# TODO: more robust tool detection
COMMAND_HG = "hg"
COMMAND_GIT = "git"
COMMAND_SVN = "svn"


def _check_return_code(code):
    if code != 0:
        raise RuntimeError("repository operation failed")


def _remove_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)


def _execute(command):
    return eos.util.execute_command(command, eos.is_verbose(), not eos.is_verbose())

# -----


def hg_repo_exists(dir):
    # TODO: more robust check
    return os.path.exists(os.path.join(dir, ".hg"))


def git_repo_exists(dir):
    # TODO: more robust check
    return os.path.exists(os.path.join(dir, ".git"))


def hg_clone(url, directory):
    return _execute(COMMAND_HG + " clone " + url + " " + directory)


def hg_pull(directory):
    return _execute(COMMAND_HG + " pull -R " + directory)


def hg_purge(directory):
    return _execute(COMMAND_HG + " purge -R " + directory + " --all --config extensions.purge=")


def hg_update_to_revision(directory, revision=None):
    if revision is None:
        revision = ""
    return _execute(COMMAND_HG + " update -R " + directory + " -C " + revision)


def hg_update_to_branch_tip(directory, branch):
    return _execute(COMMAND_HG + " update -R " + directory + " -C " + branch)

# -----


def git_clone(url, directory):
    return _execute(COMMAND_GIT + " clone --recursive " + url + " " + directory)


def git_fetch(directory):
    return _execute(COMMAND_GIT + " -C " + directory + " fetch --recurse-submodules")


def git_pull(directory):
    return _execute(COMMAND_GIT + " -C " + directory + " pull --recurse-submodules")


def git_clean(directory):
    return _execute(COMMAND_GIT + " -C " + directory + " clean -fxd")


def git_checkout(directory, branch=None):
    if branch is None:
        branch = ""  # making this effectively a no-op
    return _execute(COMMAND_GIT + " -C " + directory + " checkout " + branch)


def git_submodule_update(directory):
    return _execute(COMMAND_GIT + " -C " + directory + " submodule update")


def git_reset_to_revision(directory, revision=None):
    if revision is None:
        revision = "HEAD"
    return _execute(COMMAND_GIT + " -C " + directory + " reset --hard " + revision)

# -----


def svn_checkout(url, directory):
    return _execute(COMMAND_SVN + " checkout " + url + " " + directory)

# -----


def update_state(repo_type, url, name, dst_dir, branch=None, revision=None):
    eos.log_verbose("Updating repository for '" + name + "' (url = " + url + ", target_dir = " + dst_dir + ")")

    try:
        if repo_type == "git":
            if not git_repo_exists(dst_dir):
                _remove_directory(dst_dir)
                _check_return_code(git_clone(url, dst_dir))

            _check_return_code(git_clean(dst_dir))
            _check_return_code(git_fetch(dst_dir))

            if revision and revision != "":
                _check_return_code(git_reset_to_revision(dst_dir, revision))
            else:
                if not branch or branch == "":
                    branch = "master"
                _check_return_code(git_checkout(dst_dir, branch))
                _check_return_code(git_pull(dst_dir))
            _check_return_code(git_submodule_update(dst_dir))

        elif repo_type == "hg":
            if not hg_repo_exists(dst_dir):
                _remove_directory(dst_dir)
                _check_return_code(hg_clone(url, dst_dir))

            _check_return_code(hg_purge(dst_dir))
            _check_return_code(hg_pull(dst_dir))

            if revision and revision != "":
                _check_return_code(hg_update_to_revision(dst_dir, revision))
            else:
                if not branch or branch == "":
                    branch = "default"
                _check_return_code(hg_update_to_branch_tip(dst_dir, branch))

        elif repo_type == "svn":
            _remove_directory(dst_dir)
            _check_return_code(svn_checkout(url, dst_dir))

            if revision and revision != "":
                eos.log_error("cannot update SVN repository to revision")
                return False

        else:
            eos.log_error("unknown repository type '" + repo_type + "'")
            return False
    except RuntimeError:
        return False

    return True
