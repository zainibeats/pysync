import os


def is_path_ready(path: str, type: str, mount_point=None) -> bool:
    path = os.path.expanduser(path)
    if type == "local":
        return True
    elif type == "external":
        return bool (os.path.isdir(path))
    # Type equals NFS
    else:
        try:
            # Checks if path is mount point
            return bool (os.path.ismount(mount_point))
        except PermissionError:
            return False