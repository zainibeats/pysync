import os
import sys

from logger import logger

def is_path_ready(path: str, filesystem: str, mount_point=None) -> bool:
    path = expand_path(path)
    if filesystem == "local":
        return True
    elif filesystem == "external":
        return bool (os.path.isdir(path))
    elif filesystem == "nfs":
        try:
            # Checks if path is mount point
            return bool (os.path.ismount(expand_path(mount_point)))
        except (PermissionError, TypeError):
            return False
    else:
        logger.error(f"Unknown 'filesystem' value in the config.json!")
        return False

def confirm_with_user(preview_cmd: str) -> bool:
    attempts = 0
    while attempts < 4:
        user_input = input(f"You are about to run:\n{preview_cmd}\n\ny or n?: ").strip().lower()
        if user_input == "y":
            return True
        elif user_input == "n":
            return False
        else:
            print("Enter 'y' to proceed or 'n' to exit")
            attempts += 1            
            continue
    else:
        print("Multiple unknown inputs detected. Quitting PySync...")
        return False

# Expands path and corrects path if ran as sudo
def expand_path(path: str) -> str:
    if os.environ.get("SUDO_USER"):
        sudo_user = os.environ.get("SUDO_USER")
        sudo_user_home_prefix = "~" + sudo_user
        sudo_user_path = path.replace("~", sudo_user_home_prefix)
        full_path = os.path.expanduser(sudo_user_path)
        return full_path
    else:
        full_path = os.path.expanduser(path)
        return full_path

def validate_rsync_command(job, src_path, dst_path, src_mp, dst_mp, rsync_command) -> bool | None:
    if not is_path_ready(src_path, src_config["filesystem"], src_mp):
        logger.warning(f"Source not ready: {src_path}")
        return False
    if not is_path_ready(dst_path, dst_config["filesystem"], dst_mp):
        logger.warning(f"Destination not ready: {dst_path}")
        return False
    if "--delete" in job["flags"] and not os.listdir(src_path):
        logger.error(f"Ignoring Job '{job['name']}' because the '--delete' flag is being ran on an empty source directory")
        return False
