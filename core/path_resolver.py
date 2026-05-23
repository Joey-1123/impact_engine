import os


def module_to_file(module_name, base_dir=None):
    """
    Convert module path to file path.

    utils.helpers → utils/helpers.py
    """
    if not module_name:
        return None

    path = module_name.replace(".", os.sep) + ".py"

    if base_dir and not os.path.isabs(path):
        return os.path.normpath(os.path.join(base_dir, path))

    return os.path.normpath(path)
