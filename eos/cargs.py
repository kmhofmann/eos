import argparse
import eos


def parse():
    # parse command line arguments
    cl_parser = argparse.ArgumentParser(description='Bootstrap external libraries')
    cl_parser.add_argument("-l", "--library", action="append", help="specifies name of library to bootstrap")
    cl_parser.add_argument("-L", "--library-file", action="append",
                           help="specifies name of file containing list of library names to bootstrap")
    cl_parser.add_argument("-a", "--all", action="store_true",
                           help="bootstrap all libraries; overrides --library and --library-file")
    cl_parser.add_argument("-f", "--force", action="store_true",
                           help="force updating, i.e. disregard state file")
    cl_parser.add_argument("-j", "--json-file", default="test/libraries.json",
                           help="specifies JSON file to read library metadata from")
    cl_parser.add_argument("-p", "--postprocessing-dir",
                           help="specifies the directory that postprocessing files (patches and scripts) are in; "
                                "the default is to be assumed relative to the location of the JSON file")
    cl_parser.add_argument("-v", "--verbose", action="count",
                           help="verbose output (for debugging), increases with the number of -v arguments")
    cl_parser.add_argument("destination_dir", nargs=1)
    return cl_parser.parse_args()


def gather_library_names(names, name_files):
    libraries = []

    if names:
        libraries.extend(names)  # get all directly specified libraries

    if name_files:
        for filename in name_files:
            try:
                with open(filename) as f:
                    libraries_from_file = [l for l in (line.strip() for line in f) if l]  # get all non-empty lines
                    libraries += [l for l in libraries_from_file if l[0] is not '#']  # ignore lines with '#'
            except IOError:
                eos.log_error("parsing libraries file '" + filename + "' failed")
                raise

    return libraries
