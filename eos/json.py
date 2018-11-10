from __future__ import absolute_import
import json

from eos.log import log_error


def read_file(filename, require_file=False):
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
    return []


def write_file(filename, data):
    with open(filename, "w") as file:
        json.dump(data, file)


def get_library_names(data):
    return [name for name in (obj.get("name", None) for obj in data) if name]


def get_library_object(data, name):
    for obj in data:
        if obj.get("name", None) == name:
            return obj
    return None


def has_branch_follow_property(obj):
    if obj.get("source", None):
        src = obj["source"]
        if src.get("branch-follow", None):
            return True
    return False
