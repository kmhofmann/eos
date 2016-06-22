def check_equals(state, name, lib_obj):
    if not state:
        return False

    for state_obj in state:
        state_name = state_obj.get('name', None)
        if state_name and state_name == name and state_obj == lib_obj:
            return True
    return False


def remove_library(state, name):
    if state:
        state[:] = [s for s in state if not s.get('name', None) == name]
