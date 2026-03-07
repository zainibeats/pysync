import os
import sys
import subprocess
import json
import time

# Helper functions
from helpers import is_path_ready, prompt_user, expand_path
from logger import logger

# Backup rsync job list
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
with open(CONFIG_FILE, 'r') as file:
    data = json.load(file)
    backup_jobs = data['jobs']

# Iterates through json file and builds command
def build_rsync_command(job: dict) -> list | None:
    # Set source and destination if name matches job parameters
    src = dst = None
    source = destination = None
    src_mp = dst_mp = None

    for s in data["sources"]:
        if s["name"] == job["source"]:
            src = expand_path(s["path"])
            if s["mount_point"] is not None:
                src_mp = expand_path(s["mount_point"])
            source = s
            break 

    for d in data["destinations"]:
        if d["name"] == job["destination"]:
            dst = expand_path(d["path"])
            if d["mount_point"] is not None:
                dst_mp = expand_path(d["mount_point"])
            destination = d
            break 

    # Skip job if source or destination name not found in config
    if source is None:
        logger.error(f"Job '{job['name']}' skipped: source '{job['source']}' not found in config.")
        return
    if destination is None:
        logger.error(f"Job '{job['name']}' skipped: destination '{job['destination']}' not found in config.")
        return

    # Skip if source or destination is not ready
    if not is_path_ready(src, source["filesystem"], src_mp):
        logger.warning(f"Source not ready: {src}")
        return
    if not is_path_ready(dst, destination["filesystem"], dst_mp):
        logger.warning(f"Destination not ready: {dst}")
        return

    # Skip job if '--delete' flag is to be ran on an empty source
    if "--delete" in job["flags"] and not os.listdir(src):
        logger.error(f"Ignoring Job '{job['name']}' because the '--delete' flag is being ran on an empty source directory")
        return


    # Begin building rsync command
    rsync_args = ["rsync"] + job["flags"]
    # Add exclusion list if marked as so
    if job["exclude_from"]:
        rsync_args += ["--exclude-from", expand_path(job["exclude_from"])]
    rsync_args += [src, dst]
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

    preview = ''

    for job in backup_jobs:
        preview_cmd = build_rsync_command(job)
        if preview_cmd is None:
            logger.error(f"Could not run job {job['name']}!")
        else:
            preview_cmd = ' '.join(str(word) for word in preview_cmd)
            preview += preview_cmd + "\n"

    user_confirmed = prompt_user(preview)
    
    if user_confirmed:
        for job in backup_jobs:
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
