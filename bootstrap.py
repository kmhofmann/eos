#!/usr/bin/env python

from __future__ import print_function
import os
import sys

import eos
import eos.cargs
import eos.json


def bootstrap_library(json_obj, name, library_dir, cache_dir):
    eos.log_verbose("BOOTSTRAPPING LIBRARY '" + name + "' TO " + library_dir)

    # create directory for library
    if not os.path.exists(library_dir):
        os.mkdir(library_dir)

    src = json_obj.get('source', None)

    if src:
        pass

    return False


def main(argv):
    # parse command line arguments
    cl_args = eos.cargs.parse()

    json_filename = cl_args.json_file
    dst_dir = cl_args.destination_dir[0]
    eos.set_verbose(cl_args.verbose)

    # compile list of libraries to bootstrap
    try:
        requested_library_names = eos.cargs.gather_library_names(cl_args.library, cl_args.library_file)
    except IOError:
        return -1

    # read JSON data from file
    json_data = eos.json.read_file(json_filename, require_file=True)
    if not json_data:
        print("JSON data is empty; exiting.")
        return -1

    all_library_names = eos.json.get_library_names(json_data)

    # if '--all' is specified, get all library names from the JSON data
    if cl_args.all:
        requested_library_names = all_library_names

    if not requested_library_names:
        print("No libraries specified to bootstrap; exiting.")
        return -1

    # create destination directory, if it doesn't exist yet
    try:
        if not os.path.isdir(dst_dir):
            os.mkdir(dst_dir)
    except IOError:
        eos.log_error("could not create destination directory " + dst_dir)
        return -1

    # create cache directory, if it doesn't exist yet
    cache_dir = os.path.join(dst_dir, ".cache")
    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)

    # read cached state (if present)
    state_filename = os.path.join(dst_dir, ".state.json")
    json_data_state = eos.json.read_file(state_filename)

    # bootstrap each library, if needed
    libraries_bootstrapped = 0
    failed_libraries = []

    for name in requested_library_names:
        # skip library, if not found in JSON data
        if name not in all_library_names:
            eos.log_warning("unknown library name '" + name + "'")
            continue

        obj = eos.json.get_library_object(json_data, name)
        library_dir = os.path.join(dst_dir, name)

        # check against state
        state_equal = False
        if json_data_state:
            for state_obj in json_data_state:
                state_name = state_obj.get('name', None)
                if state_name and state_name == name and state_obj == obj and os.path.exists(library_dir):
                    state_equal = True
                    break
        if state_equal:
            eos.log_verbose("Cached state for library '" + name + "' matches; skipping bootstrapping")
            continue

        # remove cached state for library
        if json_data_state:
            json_data_state[:] = [state for state in json_data_state if not state.get('name', None) == name]

        if bootstrap_library(obj, name, library_dir, cache_dir):
            libraries_bootstrapped += 1

            # add cached state again
            json_data_state.append(obj)

            # write cached state to disk
            eos.json.write_file(state_filename, json_data_state)
        else:
            # TODO: give better errors
            failed_libraries.append(name)

    print("Bootstrapped " + str(libraries_bootstrapped) + " libraries")
    if failed_libraries:
        print("The following libraries FAILED to bootstrap:")
        print(", ".join(failed_libraries))

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))