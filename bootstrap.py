#!/usr/bin/env python

from __future__ import print_function
import argparse
import json
import os
import sys

def log(message):
    print("--- " + message)

def vlog(message):
    if VERBOSE:
        print("=== " + message)

def log_error(message):
    print("ERROR: " + message);

def read_json_file(filename, require_file=False):
    try:
        file_data = open(filename).read()
        return json.loads(file_data)
    except IOError:
        if require_file:
            log_error("opening JSON file '" + filename + "' failed.")
        return None
    except ValueError:
        log_error("parsing JSON file '" + filename + "' failed.")
        return None

def write_json_file(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file)

def check_json_data(data):
    for obj in data:
        if obj.get('name', None) is None:
            log_error("invalid JSON schema: library object missing 'name'")
            return False
    return True

def bootstrap_library(json_obj, name, library_dir, cache_dir):
    vlog("Need to bootstrap library '" + name + "' to " + library_dir)
    return True

def parse_command_line_args():
    # parse command line arguments
    cl_parser = argparse.ArgumentParser(description='Bootstrap external libraries')
    cl_parser.add_argument("-l", "--library", action="append", help="specifies name of library to bootstrap")
    cl_parser.add_argument("-L", "--library-file", action="append", help="specifies name of file containing list of library names to bootstrap")
    cl_parser.add_argument("-a", "--all", action="store_true", help="bootstrap all libraries; overrides --library and --library-file")
    cl_parser.add_argument("-j", "--json-file", default="libraries.json", help="specifies JSON file to read library metadata from")
    cl_parser.add_argument("-v", "--verbose", action="store_true", help="verbose output (for debugging)")
    cl_parser.add_argument("destination_dir", nargs=1)
    return cl_parser.parse_args()

def main(argv):
    global VERBOSE
    cl_args = parse_command_line_args()

    json_filename = cl_args.json_file
    dst_dir = cl_args.destination_dir[0]
    VERBOSE = cl_args.verbose

    # compile list of libraries to bootstrap
    libraries = cl_args.library # get all directly specified libraries
    if cl_args.library_file:
        for filename in cl_args.library_file:
            try:
                with open(filename) as f:
                    libraries_from_file = [l for l in (line.strip() for line in f) if l] # get all non-empty lines
                    libraries += [l for l in libraries_from_file if l[0] is not '#'] # ignore lines with '#' as first character
            except IOError:
                log_error("parsing libraries file '" + filename +"' failed")
                return -1

    # read JSON data from file
    json_data = read_json_file(json_filename, require_file=True)
    if not json_data:
        print("JSON data is empty; exiting.")
        return -1

    # sanity check the JSON data
    if not check_json_data(json_data):
        return -1

    # if '--all' is specified, get all library names from the JSON data
    if cl_args.all:
        libraries = [name for name in (obj.get('name', None) for obj in json_data) if name]

    if not libraries:
        libraries = []

    # create destination directory, if it doesn't exist yet
    try:
        if not os.path.isdir(dst_dir):
            os.mkdir(dst_dir)
    except IOError:
        log_error("could not create destination directory " + dst_dir)
        return -1

    # create cache directory, if it doesn't exist yet
    cache_dir = os.path.join(dst_dir, ".cache")
    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)

    # read cached state (if present)
    state_filename = os.path.join(dst_dir, ".state.json")
    json_data_state = read_json_file(state_filename)

    libraries_bootstrapped = 0
    for obj in json_data:
        # get library name
        name = obj.get('name', None)
        assert name

        # skip library, if not requested
        if not name in libraries:
            continue

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
            vlog("Cached state for library '" + name +"' matches; skipping bootstrapping")
            continue

        if bootstrap_library(obj, name, library_dir, cache_dir):
            libraries_bootstrapped += 1

    print("Bootstrapped " + str(libraries_bootstrapped) + " libraries")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))