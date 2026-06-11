# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import os
from typing import Optional


def module_to_file(module_name: str, base_dir: Optional[str] = None) -> Optional[str]:
    if not module_name:
        return None

    path = module_name.replace(".", "/") + ".py"

    if base_dir and not os.path.isabs(path):
        full_path = os.path.normpath(os.path.join(base_dir, path))
        if not os.path.isfile(full_path):
            init_path = os.path.normpath(
                os.path.join(base_dir, module_name.replace(".", "/"), "__init__.py")
            )
            if os.path.isfile(init_path):
                return init_path
        return full_path

    return os.path.normpath(path)
