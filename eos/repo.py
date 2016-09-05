import os
import shutil
import eos.log
import eos.tools
import eos.util


def _check_return_code(code):
    if code != 0:
        raise RuntimeError("repository operation failed")


def _remove_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)


def _execute(command):
    print_command = eos.verbosity() > 0
    quiet = eos.verbosity() <= 1
    return eos.util.execute_command(command, print_command, quiet)


def _execute_and_capture_output(command):
    print_command = eos.verbosity() > 0
    return eos.util.execute_command_capture_output(command, print_command)

# -----


def hg_repo_exists(directory):
    # Is a more robust check possible? https://trac.sagemath.org/ticket/12128 says no.
    return os.path.exists(os.path.join(directory, ".hg"))


def git_repo_exists(directory):
    return os.path.exists(os.path.join(directory, ".git")) and \
           _execute_and_capture_output(eos.tools.command_git() + " -C " + directory + " rev-parse --git-dir")[0] == 0


def hg_clone(url, directory):
    return _execute(eos.tools.command_hg() + " clone " + url + " " + directory)


def hg_pull(directory):
    return _execute(eos.tools.command_hg() + " pull -R " + directory)


def hg_purge(directory):
    return _execute(eos.tools.command_hg() + " purge -R " + directory + " --all --config extensions.purge=")


def hg_update_to_revision(directory, revision=None):
    if revision is None:
        revision = ""
    return _execute(eos.tools.command_hg() + " update -R " + directory + " -C " + revision)


def hg_update_to_branch_tip(directory, branch):
    return _execute(eos.tools.command_hg() + " update -R " + directory + " -C " + branch)


def hg_verify_commit_hash(directory, expected_commit_hash):
    rcode, out, err = _execute_and_capture_output(eos.tools.command_hg() + " -R " + directory + " --debug id -i")
    if rcode != 0:
        return False
    current_commit_hash = out
    hash_match = expected_commit_hash in current_commit_hash
    return hash_match

# -----


def git_clone(url, directory):
    return _execute(eos.tools.command_git() + " clone --recursive " + url + " " + directory)


def git_fetch(directory):
    return _execute(eos.tools.command_git() + " -C " + directory + " fetch --recurse-submodules")


def git_pull(directory):
    return _execute(eos.tools.command_git() + " -C " + directory + " pull --recurse-submodules")


def git_clean(directory):
    return _execute(eos.tools.command_git() + " -C " + directory + " clean -fxd")


def git_checkout(directory, branch=None):
    if branch is None:
        branch = ""  # making this effectively a no-op
    return _execute(eos.tools.command_git() + " -C " + directory + " checkout " + branch)


def git_submodule_update(directory):
    return _execute(eos.tools.command_git() + " -C " + directory + " submodule update")


def git_reset_to_revision(directory, revision=None):
    if revision is None:
        revision = "HEAD"
    return _execute(eos.tools.command_git() + " -C " + directory + " reset --hard " + revision)


def git_verify_commit_hash(directory, expected_commit_hash):
    rcode, out, err = _execute_and_capture_output(eos.tools.command_git() + " -C " + directory + " rev-parse HEAD")
    if rcode != 0:
        return False
    current_commit_hash = out
    hash_match = expected_commit_hash in current_commit_hash
    return hash_match

# -----


def svn_checkout(url, directory):
    return _execute(eos.tools.command_svn() + " checkout " + url + " " + directory)

# -----


def update_state_git(url, dst_dir, branch=None, revision=None):
    if not git_repo_exists(dst_dir):
        if url is None:
            return False
        _remove_directory(dst_dir)
        _check_return_code(git_clone(url, dst_dir))
    else:
        _check_return_code(git_clean(dst_dir))
        if url is not None:
            _check_return_code(git_fetch(dst_dir))

    if revision and revision != "":
        _check_return_code(git_reset_to_revision(dst_dir, revision))
    else:
        if not branch or branch == "":
            branch = "master"
        _check_return_code(git_checkout(dst_dir, branch))
        if url is not None:
            _check_return_code(git_pull(dst_dir))
    _check_return_code(git_submodule_update(dst_dir))

    if eos.util.is_sha1(revision) and not git_verify_commit_hash(dst_dir, revision):
        eos.log_error("SHA1 hash check failed")
        return False
    return True


def update_state_hg(url, dst_dir, branch=None, revision=None):
    if not hg_repo_exists(dst_dir):
        if url is None:
            return False
        _remove_directory(dst_dir)
        _check_return_code(hg_clone(url, dst_dir))
    else:
        _check_return_code(hg_purge(dst_dir))
        if url is not None:
            _check_return_code(hg_pull(dst_dir))

    if revision and revision != "":
        _check_return_code(hg_update_to_revision(dst_dir, revision))
    else:
        if not branch or branch == "":
            branch = "default"
        _check_return_code(hg_update_to_branch_tip(dst_dir, branch))

    if eos.util.is_sha1(revision) and not hg_verify_commit_hash(dst_dir, revision):
        eos.log_error("SHA1 hash check failed")
        return False
    return True


def update_state_svn(url, dst_dir, revision=None):
    _remove_directory(dst_dir)
    _check_return_code(svn_checkout(url, dst_dir))

    if revision and revision != "":
        eos.log_error("cannot update SVN repository to revision")
        return False
    return True


def update_state(repo_type, url, name, dst_dir, branch=None, revision=None):
    eos.log_verbose("Updating repository for '" + name + "' (url = "
                    + url if url is not None else "" + ", target_dir = " + dst_dir + ")")

    try:
        if repo_type == "git":
            success = update_state_git(url, dst_dir, branch=branch, revision=revision)
        elif repo_type == "hg":
            success = update_state_hg(url, dst_dir, branch=branch, revision=revision)
        elif repo_type == "svn":
            if url is None:
                eos.log_error("cannot execute local operations on SVN repository")
                return False
            success = update_state_svn(url, dst_dir, revision=revision)
        else:
            eos.log_error("unknown repository type '" + repo_type + "'")
            return False
    except RuntimeError:
        return False

    return success
