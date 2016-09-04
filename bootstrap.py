#!/usr/bin/env python

import os
import sys

import eos
import eos.cache
import eos.cargs
import eos.constants
import eos.json
import eos.state
import eos.tools


def main(argv):
    # parse command line arguments
    cl_args = eos.cargs.parse()

    json_filename = cl_args.json_file
    dst_dir = cl_args.destination_dir[0]
    postprocessing_dir = cl_args.postprocessing_dir
    if not postprocessing_dir:
        postprocessing_dir = os.path.dirname(os.path.abspath(json_filename))
    snapshot_dir = None  # TODO: expose as option (should be None, if no snapshots required)
    fallback_server_url = None  # TODO: expose as option (should be None, if no fallback URL specified)

    eos.set_verbosity(0 if cl_args.verbose is None else cl_args.verbose)

    # initialize tool commands
    eos.tools.initialize_commands()

    # compile list of libraries to bootstrap
    try:
        requested_library_names = eos.cargs.gather_library_names(cl_args.library, cl_args.library_file)
    except IOError:
        return -1

    # read JSON data from file
    json_data = eos.json.read_file(json_filename, require_file=True)
    if not json_data:
        eos.log("JSON data is empty; exiting.")
        return -1

    all_library_names = eos.json.get_library_names(json_data)

    # if '--all' is specified, get all library names from the JSON data
    if cl_args.all:
        requested_library_names = all_library_names

    if not requested_library_names:
        eos.log("No libraries specified to bootstrap; exiting.")
        return -1

    # create destination directory, if it doesn't exist yet
    try:
        if not os.path.isdir(dst_dir):
            os.mkdir(dst_dir)
    except IOError:
        eos.log_error("could not create destination directory " + dst_dir)
        return -1

    # initialize cache directory
    cache_dir = os.path.join(dst_dir, eos.constants.CACHE_DIR_REL)
    eos.cache.init_cache_dir(cache_dir)

    # read cached state (if present)
    state_filename = os.path.join(dst_dir, eos.constants.STATE_FILENAME)
    json_data_state = eos.json.read_file(state_filename)

    # the '--force' option cleans the cached state, such that bootstrapping will commence for each library
    if cl_args.force:
        json_data_state = []

    # bootstrap each library, if needed
    libraries_bootstrapped = 0
    libraries_skipped = 0
    failed_libraries = []

    for name in requested_library_names:
        # skip library, if not found in JSON data
        if name not in all_library_names:
            eos.log_warning("unknown library name '" + name + "'")
            continue

        obj = eos.json.get_library_object(json_data, name)
        library_dir = os.path.join(dst_dir, name)

        # check against state
        if eos.state.check_equals(json_data_state, name, obj):
            if (not eos.json.has_branch_follow_property(obj)) and os.path.exists(library_dir):
                libraries_skipped += 1
                eos.log_verbose("Cached state for library '" + name + "' matches; skipping bootstrapping")
                continue

        # remove cached state for library
        eos.state.remove_library(json_data_state, name)

        if eos.bootstrap_library(obj, name, library_dir, postprocessing_dir, snapshot_dir, fallback_server_url):
            libraries_bootstrapped += 1

            # add cached state again
            json_data_state.append(obj)

            # write cached state to disk
            eos.json.write_file(state_filename, json_data_state)
        else:
            # TODO: give better errors
            failed_libraries.append(name)

    eos.log("Bootstrapped " + str(libraries_bootstrapped) + " libraries; " + str(libraries_skipped) +
            " were already up to date.")
    if failed_libraries:
        eos.log("The following libraries FAILED to bootstrap:")
        eos.log(", ".join(failed_libraries))
        return -1

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
