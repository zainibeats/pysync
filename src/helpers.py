# helpers.py

import os


def is_path_ready(path: str) -> bool:
    if not os.path.isdir(path):
        return False
    try:
        # Checks if path is mount point
        return bool (os.path.ismount(path))
    except PermissionError:
        # Permission denied → treat as not ready
        return False
