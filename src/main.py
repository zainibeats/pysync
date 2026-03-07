import os
import sys
import subprocess
import json
import time

# Helper functions
from helpers import is_path_ready, confirm_with_user, expand_path
from logger import logger

# Backup rsync job list
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
with open(CONFIG_FILE, 'r') as file:
    config = json.load(file)
    BACKUP_JOBS = config['jobs']

# Iterates through json file and builds command
def build_rsync_command(job: dict) -> list | None:
    # Set source and destination if name matches job parameters
    src_path = dst_path = None
    src_mp = dst_mp = None
    src_config = dst_config = None

    for source_entry in config["sources"]:
        if source_entry["name"] == job["source"]:
            src_path = expand_path(source_entry["path"])
            if source_entry["mount_point"] is not None:
                src_mp = expand_path(source_entry["mount_point"])
            src_config = source_entry
            break 

    for dest_entry in config["destinations"]:
        if dest_entry["name"] == job["destination"]:
            dst_path = expand_path(dest_entry["path"])
            if dest_entry["mount_point"] is not None:
                dst_mp = expand_path(dest_entry["mount_point"])
            dst_config = dest_entry
            break 

    # Skip job if source or destination name not found in config
    if src_config is None:
        logger.error(f"Job '{job['name']}' skipped: source '{job['source']}' not found in config.")
        return
    if dst_config is None:
        logger.error(f"Job '{job['name']}' skipped: destination '{job['destination']}' not found in config.")
        return

    # Skip if source or destination is not ready
    if not is_path_ready(src_path, src_config["filesystem"], src_mp):
        logger.warning(f"Source not ready: {src_path}")
        return
    if not is_path_ready(dst_path, dst_config["filesystem"], dst_mp):
        logger.warning(f"Destination not ready: {dst_path}")
        return

    # Skip job if '--delete' flag is to be ran on an empty source
    if "--delete" in job["flags"] and not os.listdir(src_path):
        logger.error(f"Ignoring Job '{job['name']}' because the '--delete' flag is being ran on an empty source directory")
        return


    # Begin building rsync command
    rsync_args = ["rsync"] + job["flags"]
    # Add exclusion list if marked as so
    if job["exclude_from"]:
        rsync_args += ["--exclude-from", expand_path(job["exclude_from"])]
    rsync_args += [src_path, dst_path]
    return rsync_args

# Runs each rsync command
def run_rsync_job(rsync_command: list, job: dict) -> None:
    # Logs upcoming rsync command
    print("Running rsync commands...")
    logger.info(f"Running rsync: {' '.join(rsync_command)}")
    try:
        # Execute the rsync command, capturing output and raising on error
        result = subprocess.run(
            rsync_command,
            capture_output=True,
            text=True,
            check=True,
        )
        # Log success and any stdout returned by rsync
        logger.info(f"Job {job['name']} succeeded! {result.stdout}")
    except subprocess.CalledProcessError as exc:
        # Log failure details including exit code, stdout, and stderr
        logger.error(
            f"Job {job['name']} failed (exit {exc.returncode}):\n"
            f"stdout: {exc.stdout}\nstderr: {exc.stderr}"
        )

# Main loop
def main() -> None:

    preview_text = ''

    for job in BACKUP_JOBS:
        rsync_command = build_rsync_command(job)
        if rsync_command is None:
            logger.error(f"Could not run job {job['name']}!")
        else:
            rsync_command = ' '.join(str(arg) for arg in rsync_command)
            preview_text += rsync_command + "\n"

    user_confirmed = confirm_with_user(preview_text)
    
    if user_confirmed:
        for job in BACKUP_JOBS:
            rsync_command = build_rsync_command(job)
            if rsync_command is None:
                logger.error(f"Could not run job {job['name']}!")
            else:
                run_rsync_job(rsync_command, job)
        time.sleep(3)
        print("Syncing complete!")
        sys.exit()
    else:
        print("Quitting PySync...")
        sys.exit()


if __name__ == "__main__":
    main()
