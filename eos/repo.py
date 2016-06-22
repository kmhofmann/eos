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

# -----


def hg_repo_exists(dir):
    # TODO: more robust check
    return os.path.exists(os.path.join(dir, ".hg"))


def git_repo_exists(dir):
    # TODO: more robust check
    return os.path.exists(os.path.join(dir, ".git"))


def hg_clone(url, directory):
    return eos.util.execute_command(COMMAND_HG + " clone " + url + " " + directory, eos.is_verbose())


def hg_pull(directory):
    return eos.util.execute_command(COMMAND_HG + " pull -R " + directory, eos.is_verbose())


def hg_purge(directory):
    return eos.util.execute_command(COMMAND_HG + " purge -R " + directory + " --all --config extensions.purge=", eos.is_verbose())


def hg_update_to_revision(directory, revision=None):
    if revision is None:
        revision = ""
    return eos.util.execute_command(COMMAND_HG + " update -R " + directory + " -C " + revision, eos.is_verbose())


def hg_update_to_branch_tip(directory, branch):
    return eos.util.execute_command(COMMAND_HG + " update -R " + directory + " -C " + branch, eos.is_verbose())

# -----


def git_clone(url, directory):
    return eos.util.execute_command(COMMAND_GIT + " clone --recursive " + url + " " + directory, eos.is_verbose())


def git_fetch(directory):
    return eos.util.execute_command(COMMAND_GIT + " -C " + directory + " fetch --recurse-submodules", eos.is_verbose())


def git_pull(directory):
    return eos.util.execute_command(COMMAND_GIT + " -C " + directory + " pull --recurse-submodules", eos.is_verbose())


def git_clean(directory):
    return eos.util.execute_command(COMMAND_GIT + " -C " + directory + " clean -fxd", eos.is_verbose())


def git_checkout(directory, branch=None):
    if branch is None:
        branch = ""  # making this effectively a no-op
    return eos.util.execute_command(COMMAND_GIT + " -C " + directory + " checkout " + branch, eos.is_verbose())


def git_reset_to_revision(directory, revision=None):
    if revision is None:
        revision = "HEAD"
    return eos.util.execute_command(COMMAND_GIT + " -C " + directory + " reset --hard " + revision, eos.is_verbose())

# -----


def svn_checkout(url, directory):
    return eos.util.execute_command(COMMAND_SVN + " checkout " + url + " " + directory)

# -----


def update_state(repo_type, url, name, dst_dir, branch=None, revision=None):
    eos.log("Updating repository for '" + name + "' (url = " + url + ", target_dir = " + dst_dir + ")")

    try:
        if repo_type == "git":
            if not git_repo_exists(dst_dir):
                remove_directory(dst_dir)
                check_return_code(git_clone(url, dst_dir))

            check_return_code(git_clean(dst_dir))
            check_return_code(git_fetch(dst_dir))

            if revision and revision != "":
                check_return_code(git_reset_to_revision(dst_dir, revision))
            else:
                if not branch or branch == "":
                    branch = "master"
                check_return_code(git_checkout(dst_dir, branch))
                check_return_code(git_pull(dst_dir))

        elif repo_type == "hg":
            if not hg_repo_exists(dst_dir):
                remove_directory(dst_dir)
                check_return_code(hg_clone(url, dst_dir))

            check_return_code(hg_purge(dst_dir))
            check_return_code(hg_pull(dst_dir))

            if revision and revision != "":
                check_return_code(hg_update_to_revision(dst_dir, revision))
            else:
                if not branch or branch == "":
                    branch = "default"
                check_return_code(hg_update_to_branch_tip(dst_dir, branch))

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
