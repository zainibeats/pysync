import os
import sys
import subprocess
import json

from helpers import confirm_with_user, expand_path, resolve_job_paths
from logger import logger
from validators import validate_config, validate_rsync_command

# Iterates through json file and builds command
def build_rsync_command(job: dict, resolved_paths: dict) -> list:
    rsync_args = ["rsync"] + job['flags']
    # Add exclusion list if marked as so
    if job['exclude_from']:
        rsync_args += ["--exclude-from", expand_path(job['exclude_from'])]
    rsync_args += [resolved_paths['src_path'], resolved_paths['dst_path']]
    return rsync_args

# Runs each rsync command
def run_rsync_job(job: dict, rsync_command: list) -> None:
    # Logs upcoming rsync command
    logger.info(f"Running job {job['name']}...")
    logger.debug(f"Running command: {' '.join(rsync_command)}")
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

def load_config() -> dict | None : 
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
            return config
    except FileNotFoundError as e:
        logger.error("Config file not found. Make sure a config.json exists in the pysync directory.")
        return None

# Main loop
def main() -> None:

    # Load config and quit program if none found
    current_config = load_config()
    if current_config is None:
        logger.info("Quitting PySync...")
        sys.exit(1)
    
    # Validate config and quit program if not validated
    validated_config = validate_config(current_config)
    if not validated_config:
        logger.info("Quitting PySync...")
        sys.exit(1)
    # If config is successfully validated, assign jobs listed in config.json to backup_jobs
    else:
        backup_jobs = current_config['jobs']

    # Initialize values
    proposed_commands = ''
    valid_jobs = []

    # Loops through jobs, get necessary paths for each one, builds command, validates, and creates list of valid jobs
    for job in backup_jobs:
        resolved_paths = resolve_job_paths(job, current_config)
        if resolved_paths['src_config'] is None:
            logger.error(f"Job '{job['name']}' skipped: source '{job['source']}' not found in config.")
        elif resolved_paths['dst_config'] is None:
            logger.error(f"Job '{job['name']}' skipped: destination '{job['destination']}' not found in config.")
        else:
            rsync_command = build_rsync_command(job, resolved_paths)
            is_command_valid = validate_rsync_command(job, resolved_paths)
            if is_command_valid:
                valid_jobs.append((job, rsync_command, resolved_paths))

    # Loops through validated jobs, converts into strings
    for job, rsync_command, resolved_paths in valid_jobs:
        rsync_command = ' '.join(str(arg) for arg in rsync_command)
        proposed_commands += rsync_command + "\n"

    if not valid_jobs:
        logger.error("No jobs to run!")
        logger.info("Quitting PySync...")
        sys.exit(1)
    else:
        user_confirmed = confirm_with_user(proposed_commands)

        # Loop through jobs, re-vaidate, and run 
        if user_confirmed:
            for job, rsync_command, resolved_paths in valid_jobs:
                is_command_valid = validate_rsync_command(job, resolved_paths)            
                if is_command_valid:
                    run_rsync_job(job, rsync_command)
            logger.info("Syncing complete!")
            sys.exit(0)
        else:
            logger.info("Quitting PySync...")
            sys.exit(0)

if __name__ == "__main__":
    main()
