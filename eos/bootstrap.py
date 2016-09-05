import os
import shutil
import eos.archive
import eos.cache
import eos.log
import eos.post
import eos.repo
import eos.util


def bootstrap_library(json_obj, name, library_dir, postprocessing_dir):
    eos.log("Bootstrapping library '" + name + "' to " + library_dir)

    # create directory for library
    if not os.path.exists(library_dir):
        os.mkdir(library_dir)

    # get library

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

    # post-process library

    post = json_obj.get('postprocess', None)
    if not post:
        return True  # it's optional

    post_type = post.get('type', None)
    if not post_type:
        eos.log_error("postprocessing object for library '" + name + "' must have a 'type'")
        return False

    post_file = post.get('file', None)
    if not post_file:
        eos.log_error("postprocessing object for library '" + name + "' must have a 'file'")
        return False

    if post_type not in ['patch', 'script']:
        eos.log_error("unknown postprocessing type for library '" + name + "'")
        return False

    # If we have a postprocessing directory specified, make it an absolute path
    if postprocessing_dir:
        post_file = os.path.join(postprocessing_dir, post_file)

    if post_type == "patch":
        pnum = post.get('pnum', 2)
        # Try to apply patch
        if not eos.post.apply_patch(name, library_dir, post_file, pnum):
            eos.log_error("patch application of " + post_file + " failed for library '" + name + "'")
            return False
    elif post_type == "script":
        # Try to run script
        if not eos.post.run_script(name, post_file):
            eos.log_error("script execution of " + post_file + " failed for library '" + name + "'")
            return False

    return True

