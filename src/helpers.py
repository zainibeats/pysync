# helpers.py

import os


def is_path_ready(path: str, external: bool) -> bool:
    path = os.path.expanduser(path)
    if not os.path.isdir(path):
        return False
    if not external:
        return True
    try:
        # Checks if path is mount point
        return bool (os.path.ismount(path))
    except PermissionError:
        # Permission denied → treat as not ready
        return False
