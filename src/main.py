import os
import sys
import subprocess
import json
import time

# Helper functions
from helpers import is_path_ready, confirm_with_user, expand_path, resolve_job_paths
from logger import logger

# Backup rsync job list
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
with open(CONFIG_FILE, 'r') as file:
    config = json.load(file)
    BACKUP_JOBS = config['jobs']

# Iterates through json file and builds command
def build_rsync_command(job: dict, resolved_paths: dict) -> list | None:
    rsync_args = ["rsync"] + job['flags']
    # Add exclusion list if marked as so
    if job['exclude_from']:
        rsync_args += ["--exclude-from", expand_path(job['exclude_from'])]
    rsync_args += [resolved_paths['src_path'], resolved_paths['dst_path']]
    return rsync_args


def validate_rsync_command(job: dict, resolved_paths: dict) -> bool | None:
    if not is_path_ready(resolved_paths['src_path'], resolved_paths['src_config']['filesystem'], resolved_paths['src_mp']):
        logger.warning(f"Source not ready: {resolved_paths['src_path']}")
        return False
    elif not is_path_ready(resolved_paths['dst_path'], resolved_paths['dst_config']['filesystem'], resolved_paths['dst_mp']):
        logger.warning(f"Destination not ready: {resolved_paths['dst_path']}")
        return False
    # Checks if '--delete' flag is to be ran on an empty source 
    elif "--delete" in job['flags'] and not os.listdir(resolved_paths['src_path']):
        logger.error(f"Ignoring Job '{job['name']}' because the '--delete' flag is being ran on an empty source directory")
        return False
    else:
        return True

# Runs each rsync command
def run_rsync_job(job: dict, rsync_command: list) -> None:
    # Logs upcoming rsync command
    print(f"Running job {job['name']}...")
    logger.info(f"Running command: {' '.join(rsync_command)}")
    try:
        # Execute the rsync command, capturing output and raising on error
        result = subprocess.run(
            rsync_command,
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"Job {job['name']} succeeded!")
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

    proposed_commands = ''
    valid_jobs = []

    # Loops through jobs, get necessary paths for each one, builds command, validates, and creates list of valid jobs
    for job in BACKUP_JOBS:
        resolved_paths = resolve_job_paths(job, config)
        rsync_command = build_rsync_command(job, resolved_paths)
        # Error handling
        if resolved_paths['src_config'] is None:
            logger.error(f"Job '{job['name']}' skipped: source '{job['source']}' not found in config.")
        elif resolved_paths['dst_config'] is None:
            logger.error(f"Job '{job['name']}' skipped: destination '{job['destination']}' not found in config.")
        elif rsync_command is None:
            logger.error(f"Could not run job {job['name']}!")
        else:
            
            is_command_valid = validate_rsync_command(job, resolved_paths)
            if is_command_valid:
                valid_jobs.append((job, rsync_command, resolved_paths))
            else:
                logger.warning(f"Source not ready: {resolved_paths['src_path']}")

    # Loops through validated jobs, converts into strings
    for job, rsync_command, resolved_paths in valid_jobs:
        rsync_command = ' '.join(str(arg) for arg in rsync_command)
        proposed_commands += rsync_command + "\n"

    user_confirmed = confirm_with_user(proposed_commands)

    # Loop through jobs, re-vaidate, and run 
    if user_confirmed:
        for job, rsync_command, resolved_paths in valid_jobs:
            is_command_valid = validate_rsync_command(job, resolved_paths)            
            if is_command_valid:
                run_rsync_job(job, rsync_command)
            else:
                logger.warning(f"Source not ready: {resolved_paths['src_path']}")
        time.sleep(3)
        print("Syncing complete!")
        sys.exit()
    else:
        print("Quitting PySync...")
        sys.exit()

if __name__ == "__main__":
    main()
