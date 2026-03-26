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

def validate_config(config: dict) -> bool:
    # CHecks for 'sources' key in config.json
    sources = config.get('sources')
    if sources is None:
        logger.error(f"Missing 'sources' key in config.json!")
        return False
    else:
        for source in sources:
            name = source.get('name')
            if name is None:
                logger.error(f"Missing 'name' key for source {source} in config.json!")       
                return False
            path = source.get('path')
            if path is None:
                logger.error(f"Missing 'path' key for source {name} in config.json!")
                return False
            filesystem = source.get('filesystem')
            if filesystem is None:
                logger.error(f"Missing 'filesystem' key for source {name} in config.json!")
                return False
            if 'mount_point' not in source:
                logger.error(f"Missing 'mount_point' key for source {name} in config.json!")
                return False
            else:
                if filesystem == 'nfs':
                    mount_point = source['mount_point']
                    if mount_point is None:
                        logger.error(f"Missing 'mount_point' key for nfs source {name} in config.json! NFS shares must have a defined mount point.")
                        return False

    # Checks for 'destinations' key in config.json
    destinations = config.get('destinations')
    if destinations is None:
        logger.error(f"Missing 'destinations' key in config.json!")
        return False
    else:
        for destination in destinations:
            name = destination.get('name')
            if name is None:
                logger.error(f"Missing 'name' key for destination {destination} in config.json!")       
                return False
            path = destination.get('path')
            if path is None:
                logger.error(f"Missing 'path' key for destination {name} in config.json!")
                return False
            filesystem = destination.get('filesystem')
            if filesystem is None:
                logger.error(f"Missing 'filesystem' key for destination {name} in config.json!")
                return False
            if 'mount_point' not in destination:
                logger.error(f"Missing 'mount_point' key for destination {name} in config.json!")
                return False
            else:
                if filesystem == 'nfs':
                    mount_point = destination['mount_point']
                    if mount_point is None:
                        logger.error(f"Missing 'mount_point' key for nfs destination {name} in config.json! NFS shares must have a defined mount point.")
                        return False

    # Checks for 'jobs' key in config.json
    jobs = config.get('jobs')
    if jobs is None:
        logger.error(f"Missing 'jobs' key in config.json!")
        return False
    else:
        for job in jobs:
            name = job.get('name')
            if name is None:
                logger.error(f"Missing 'name' key for job {job} in config.json!")       
                return False
            source = job.get('source')
            if source is None:
                logger.error(f"Missing 'source' key for job {name} in config.json!")
                return False
            destination = job.get('destination')
            if destination is None:
                logger.error(f"Missing 'destination' key for job {name} in config.json!")
                return False
            if 'exclude_from' not in job:
                logger.error(f"Missing 'exclude_from' key for job {name} in config.json!")
                return False
            if 'flags' not in job:
                logger.error(f"Missing 'flags' key for job {name} in config.json!")
                return False

    return True

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
