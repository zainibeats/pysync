import os
import sys

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
            return bool (os.path.ismount(os.path.expanduser(mount_point)))
        except (PermissionError, TypeError):
            return False


def prompt_user(hr_cmd: str) -> bool:
    user_input = input(f"You are about to run:\n{hr_cmd}\n\ny or n?: ").strip().lower()
    if user_input == "y":
        return True
    elif user_input == "n":
        sys.exit()
    else:
        print("Enter 'y' to proceed or 'n' to exit")
        continue


