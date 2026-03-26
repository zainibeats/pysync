import os
import sys

from logger import logger

def is_path_ready(path: str, filesystem: str, mount_point=None) -> bool:
    path = expand_path(path)
    if filesystem == "local":
        return bool (os.path.isdir(path))
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

def resolve_job_paths(job: dict, config: dict) ->  dict:
    
    # Initialize variable
    src_path = dst_path = None
    src_mp = dst_mp = None
    src_config = dst_config = None

    # Set source and destination if "name" matches "job" parameters from config file
    for source_entry in config['sources']:
        if source_entry['name'] == job['source']:
            src_path = expand_path(source_entry['path'])
            if source_entry['mount_point'] is not None:
                src_mp = expand_path(source_entry['mount_point'])
            src_config = source_entry
            break 

    for dest_entry in config["destinations"]:
        if dest_entry['name'] == job['destination']:
            dst_path = expand_path(dest_entry['path'])
            if dest_entry['mount_point'] is not None:
                dst_mp = expand_path(dest_entry['mount_point'])
            dst_config = dest_entry
            break 

    return {
        "src_path": src_path, 
        "dst_path": dst_path, 
        "src_mp": src_mp, 
        "dst_mp": dst_mp, 
        "src_config": src_config, 
        "dst_config": dst_config
        }
