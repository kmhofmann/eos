import os
import shutil

import eos.archive
import eos.cache
import eos.constants
import eos.fallback
import eos.log
import eos.post
import eos.repo
import eos.util


def bootstrap_library(
    json_obj,
    name,
    library_dir,
    postprocessing_dir,
    create_snapshots=False,
    fallback_server_url=None,
    force_fallback=False,
):
    eos.log("Bootstrapping library '" + name + "' to " + library_dir)

    # create directory for library
    if not os.path.exists(library_dir):
        os.mkdir(library_dir)

    # get library

    src = json_obj.get("source", None)
    if not src:
        eos.log_warning("library '" + name + "' is missing source description")
        return False

    src_type = src.get("type", None)
    src_url = src.get("url", None)

    if not src_type or not src_url:
        eos.log_warning("library '" + name + "' is missing type or URL description")
        return False

    if src_type not in ["archive", "git", "hg", "svn", "file"]:
        eos.log_warning("unknown source type for library '" + name + "'")
        return False

    def get_from_fallback(filename, relative_src_dir, download_dir, extract_file=True):
        if fallback_server_url is None:
            return False
        eos.log("Downloading from fallback URL %s" % fallback_server_url)
        relative_src_dir = eos.util.convert_to_forward_slashes(relative_src_dir)
        success = eos.fallback.download_from_fallback_url(
            fallback_server_url,
            filename,
            relative_src_dir=relative_src_dir,
            download_dir=download_dir if extract_file else library_dir,
            extract_dir=library_dir if extract_file else None,
        )
        if not success:
            eos.log_error("download from fallback URL failed")
        return success

    if src_type == "file":
        # We're dealing with a single-file uncompressed library
        sha1_hash = src.get("sha1", None)
        user_agent = src.get("user-agent", None)

        if force_fallback:
            return get_from_fallback(
                eos.util.get_filename_from_url(eos.util.sanitize_url(src_url)),
                eos.cache.get_relative_archive_dir(name),
                eos.cache.get_archive_dir(name),
                extract_file=False,
            )

            # download file
        download_filename = eos.util.download_file(src_url, eos.cache.get_archive_dir(name), sha1_hash, user_agent)
        if download_filename == "":
            eos.log_error("downloading of file for '" + name + "' from " + src_url + " failed")
            return get_from_fallback(
                os.path.basename(download_filename),
                eos.cache.get_relative_archive_dir(name),
                eos.cache.get_archive_dir(name),
                extract_file=False,
            )

            if os.path.exists(library_dir):
                shutil.rmtree(library_dir)

        # copy file
        try:
            os.mkdir(library_dir)
            filename_rel = os.path.basename(download_filename)
            shutil.copyfile(download_filename, os.path.join(library_dir, filename_rel))
        except:
            eos.log_error("copying of file for '" + download_filename + "' failed")
            if os.path.exists(library_dir):
                shutil.rmtree(library_dir)
            return False

    elif src_type == "archive":
        # We're dealing with an archive file
        sha1_hash = src.get("sha1", None)
        user_agent = src.get("user-agent", None)

        if force_fallback:
            return get_from_fallback(
                eos.util.get_filename_from_url(eos.util.sanitize_url(src_url)),
                eos.cache.get_relative_archive_dir(name),
                eos.cache.get_archive_dir(name),
            )

            # download archive file
        download_filename = eos.util.download_file(src_url, eos.cache.get_archive_dir(name), sha1_hash, user_agent)
        if download_filename == "":
            eos.log_error("downloading of file for '" + name + "' from " + src_url + " failed")
            return get_from_fallback(
                os.path.basename(download_filename),
                eos.cache.get_relative_archive_dir(name),
                eos.cache.get_archive_dir(name),
            )

            if os.path.exists(library_dir):
                shutil.rmtree(library_dir)

        # extract archive file
        if not eos.archive.extract_file(download_filename, library_dir):
            eos.log_error("extraction of file for '" + download_filename + "' failed")
            return get_from_fallback(
                os.path.basename(download_filename),
                eos.cache.get_relative_archive_dir(name),
                eos.cache.get_archive_dir(name),
            )
    else:
        # We're dealing with a repository
        branch = src.get("branch", None)
        if not branch:
            branch = src.get("branch-follow", None)
        revision = src.get("revision", None)

        if branch and revision:
            eos.log_error("cannot specify both branch (to follow) and revision for repository '" + name + "'")
            return False

        # filename for reading/writing snapshots
        snapshot_archive_name = name + ".tar.gz"
        if revision is not None:
            snapshot_archive_name = name + "_" + revision + ".tar.gz"  # add the revision number, if present

        # clone or update repository
        if not force_fallback:
            update_repo_success = eos.repo.update_state(src_type, src_url, name, library_dir, branch, revision)
        if force_fallback or not update_repo_success:
            if not force_fallback:
                eos.log_error("updating repository state for '" + name + " failed")
            fallback_success = get_from_fallback(
                snapshot_archive_name, eos.cache.get_relative_snapshot_dir(), eos.cache.get_snapshot_dir()
            )
            if not fallback_success:
                return False
            fallback_success = eos.repo.update_state(src_type, None, name, library_dir, branch, revision)
            if not fallback_success:
                eos.log_error("updating state from downloaded repository from fallback URL failed")
                return False

        # optionally create snapshot
        if create_snapshots:
            eos.log("Creating snapshot of '" + name + "' repository...")
            snapshot_archive_filename = os.path.join(eos.cache.get_snapshot_dir(), snapshot_archive_name)
            eos.log_verbose("Snapshot will be written to " + snapshot_archive_filename)
            eos.archive.create_archive_from_directory(library_dir, snapshot_archive_filename, revision is None)

    # post-process library

    postprocess_keys = sorted([key for key in json_obj if key.startswith("postprocess")])

    for postprocess_key in postprocess_keys:
        post = json_obj.get(postprocess_key, None)
        eos.log_verbose("Post-processing step '%s'" % postprocess_key)

        post_type = post.get("type", None)
        if not post_type:
            eos.log_error("postprocessing object for library '" + name + "' must have a 'type'")
            return False

        post_file = post.get("file", None)
        if not post_file:
            eos.log_error("postprocessing object for library '" + name + "' must have a 'file'")
            return False

        if post_type not in ["patch", "script"]:
            eos.log_error("unknown postprocessing type for library '" + name + "'")
            return False

        # If we have a postprocessing directory specified, make it an absolute path
        if postprocessing_dir:
            post_file = os.path.join(postprocessing_dir, post_file)

        if post_type == "patch":
            pnum = post.get("pnum", 2)
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
