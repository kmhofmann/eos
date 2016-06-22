import os
import shutil
import eos.archive
import eos.cache
import eos.log
import eos.repo
import eos.util


def bootstrap_library(json_obj, name, library_dir):
    eos.log("Bootstrapping library '" + name + "' to " + library_dir)

    # create directory for library
    if not os.path.exists(library_dir):
        os.mkdir(library_dir)

    src = json_obj.get('source', None)
    if not src:
        eos.log_warning("library '" + name + "' is missing source description")
        return False

    src_type = src.get('type', None)
    src_url = src.get('url', None)

    if not src_type or not src_url:
        eos.log_warning("library '" + name + "' is missing type or URL description")
        return False

    if src_type not in ['archive', 'git', 'hg', 'svn']:
        eos.log_warning("unknown source type for library '" + name)
        return False

    if src_type == "archive":
        sha1_hash = src.get('sha1', None)
        user_agent = src.get('user-agent', None)

        download_filename = eos.util.download_file(src_url, eos.cache.get_archive_dir(), sha1_hash, user_agent)
        if download_filename == "":
            eos.log_error("downloading of file for '" + name + "' from " + src_url + " failed")
            return False

        if os.path.exists(library_dir):
            shutil.rmtree(library_dir)

        if not eos.archive.extract_file(download_filename, library_dir):
            eos.log_error("extraction of file for '" + download_filename + "' failed")
            return False

        return True
    else:
        branch = src.get('branch', None)
        if not branch:
            branch = src.get('branch-follow', None)
        revision = src.get('revision', None)

        if branch and revision:
            eos.log_error("cannot specify both branch (to follow) and revision for repository '" + name + "'")
            return False

        if not eos.repo.update_state(src_type, src_url, name, library_dir, branch, revision):
            eos.log_error("updating repository state for '" + name + " failed")
            return False

        return True
