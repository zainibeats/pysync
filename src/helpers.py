import os

from logger import logger


def is_path_ready(path: str, filesystem: str, mount_point=None) -> bool:
    path = expand_path(path)
    # If labeled as local or external, check if directory exists
    if filesystem in ("local", "external"):
        return bool(os.path.isdir(path))
    elif filesystem == "nfs":
        try:
            # Checks if path is mount point
            return bool(os.path.ismount(expand_path(mount_point)))
        except (PermissionError, TypeError):
            return False
    else:
        logger.error("Unknown 'filesystem' value in the config.json!")
        return False


def confirm_with_user(preview_cmd: str) -> bool:
    attempts = 0
    while attempts < 4:
        user_input = (
            input(f"You are about to run:\n{preview_cmd}\n\ny or n?: ").strip().lower()
        )
        if user_input == "y":
            return True
        elif user_input == "n":
            return False
        else:
            logger.info("Enter 'y' to proceed or 'n' to exit")
            attempts += 1
            continue
    else:
        logger.warning("Multiple unknown inputs detected. Quitting PySync...")
        return False


# Expands path dynamically by checking if ran as sudo
def expand_path(path: str) -> str:
    if os.environ.get("SUDO_USER") and path.startswith("~"):
        sudo_user = os.environ.get("SUDO_USER")
        sudo_user_home_prefix = "~" + sudo_user
        # Replaces "~" prefix with sudo user $HOME (e.g. /home/john instead of /root). Expand $HOME afterwards
        full_path = os.path.expanduser(path.replace("~", sudo_user_home_prefix, 1))
        return full_path
    else:
        # Not ran as sudo -> expand path as normal
        return os.path.expanduser(path)


def resolve_job_paths(job: dict, current_config: dict) -> dict:

    # Initialize variable
    src_path = dst_path = None
    src_mp = dst_mp = None
    src_config = dst_config = None

    # Set source and destination if "name" matches "job" parameters from config file
    for source_entry in current_config["sources"]:
        if source_entry["name"] == job["source"]:
            src_path = expand_path(source_entry["path"])
            if source_entry["mount_point"] is not None:
                src_mp = expand_path(source_entry["mount_point"])
            src_config = source_entry
            break

    for dest_entry in current_config["destinations"]:
        if dest_entry["name"] == job["destination"]:
            dst_path = expand_path(dest_entry["path"])
            if dest_entry["mount_point"] is not None:
                dst_mp = expand_path(dest_entry["mount_point"])
            dst_config = dest_entry
            break

    return {
        "src_path": src_path,
        "dst_path": dst_path,
        "src_mp": src_mp,
        "dst_mp": dst_mp,
        "src_config": src_config,
        "dst_config": dst_config,
    }
