import os


def module_to_file(module_name):
    """
    Convert module path to file path.
    
    utils.helpers → utils/helpers.py
    """
    if not module_name:
        return None

    path = module_name.replace(".", "/") + ".py"
    return path