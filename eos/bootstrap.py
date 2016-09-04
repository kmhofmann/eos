import os
import shutil
import eos.archive
import eos.cache
import eos.fallback
import eos.log
import eos.post
import eos.repo
import eos.util


def bootstrap_library(json_obj, name, library_dir, postprocessing_dir, snapshot_dir, fallback_server_url):
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

    def get_archive_from_fallback(url):
        if fallback_server_url is None:
            return False
        eos.log("trying download from fallback URL %s..." % fallback_server_url)
        filename = eos.util.get_filename_from_url(eos.util.sanitize_url(url))
        fallback_success = eos.fallback.download_and_extract_archive_from_fallback_url(
            fallback_server_url, filename, eos.cache.get_archive_dir(), sha1_hash)
        return fallback_success

    def get_repository_from_fallback():
        if fallback_server_url is None:
            return False
        eos.log("trying download from fallback URL %s..." % fallback_server_url)
        # TODO: IMPLEMENT
        return False

    if src_type == "archive":
        # We're dealing with an archive file
        sha1_hash = src.get('sha1', None)
        user_agent = src.get('user-agent', None)

        download_filename = eos.util.download_file(src_url, eos.cache.get_archive_dir(), sha1_hash, user_agent)
        if download_filename == "":
            eos.log_error("downloading of file for '" + name + "' from " + src_url + " failed")
            return get_archive_from_fallback(src_url)

        if os.path.exists(library_dir):
            shutil.rmtree(library_dir)

        if not eos.archive.extract_file(download_filename, library_dir):
            eos.log_error("extraction of file for '" + download_filename + "' failed")
            return get_archive_from_fallback(src_url)
    else:
        # We're dealing with a repository
        branch = src.get('branch', None)
        if not branch:
            branch = src.get('branch-follow', None)
        revision = src.get('revision', None)

        if branch and revision:
            eos.log_error("cannot specify both branch (to follow) and revision for repository '" + name + "'")
            return False

        if not eos.repo.update_state(src_type, src_url, name, library_dir, branch, revision):
            eos.log_error("updating repository state for '" + name + " failed")
            get_repository_from_fallback()  # TODO: IMPLEMENT
            return

        if snapshot_dir:
            eos.log("Creating snapshot of '" + name + "' repository...")
            archive_name = name + ".tar.gz"  # for reading or writing of snapshot archives
            if revision is not None:
                archive_name = name + "_" + revision + ".tar.gz"
            archive_filename = os.path.join(snapshot_dir, archive_name)
            eos.archive.create_archive_from_directory(library_dir, archive_filename, revision is None)

    # post-process library

    postprocess_keys = sorted([key for key in json_obj if key.startswith('postprocess')])

    for postprocess_key in postprocess_keys:
        post = json_obj.get(postprocess_key, None)
        eos.log_verbose("Post-processing step '%s'" % postprocess_key)

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
            # Replace variable strings with contents
            post_file = post_file.replace("$LIBRARY_DIR", os.path.abspath(library_dir))
            # Try to run script
            if not eos.post.run_script(name, post_file):
                eos.log_error("script execution of " + post_file + " failed for library '" + name + "'")
                return False

    return True

