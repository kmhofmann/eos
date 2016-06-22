import os
import eos.cache
import eos.log
import eos.repo
import eos.util


def bootstrap_library(json_obj, name, library_dir):
    eos.log_verbose("")
    eos.log_verbose("")
    eos.log_verbose("BOOTSTRAPPING LIBRARY '" + name + "' TO " + library_dir)
    eos.log_verbose("")

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

        if not eos.util.download_file(src_url, eos.cache.get_archive_dir(), sha1_hash):
            eos.log_error("downloading of file for '" + name + "' from " + src_url + " failed")
            return False

        # TODO: implement file extraction
        eos.log_error("IMPLEMENTATION OF ARCHIVE BOOTSTRAPPING NOT FINISHED YET")
        return False
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
