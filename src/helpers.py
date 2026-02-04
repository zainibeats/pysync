# helpers.py

import os


def is_path_ready(path: str) -> bool:
    if not os.path.isdir(path):
        return False
    try:
        # Quick check for non-empty
        return bool(os.listdir(path))
    except PermissionError:
        # Permission denied → treat as not ready
        return False
