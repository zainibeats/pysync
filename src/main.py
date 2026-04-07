import sys

from config_loader import load_config
from executor import run_rsync_job
from helpers import confirm_with_user, resolve_job_paths
from logger import logger
from validators import build_rsync_command, validate_config, validate_rsync_command


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
        backup_jobs = current_config["jobs"]

    # Initialize values
    proposed_commands = ""
    valid_jobs = []

    # Loops through jobs, get necessary paths for each one, builds command, validates, and creates list of valid jobs
    for job in backup_jobs:
        resolved_paths = resolve_job_paths(job, current_config)
        if resolved_paths["src_config"] is None:
            logger.error(
                f"Job '{job['name']}' skipped: source '{job['source']}' not found in config."
            )
        elif resolved_paths["dst_config"] is None:
            logger.error(
                f"Job '{job['name']}' skipped: destination '{job['destination']}' not found in config."
            )
        else:
            rsync_command = build_rsync_command(job, resolved_paths)
            is_command_valid = validate_rsync_command(job, resolved_paths)
            if is_command_valid:
                valid_jobs.append((job, rsync_command, resolved_paths))

    # Loops through validated jobs, converts into strings
    for job, rsync_command, resolved_paths in valid_jobs:
        rsync_command = " ".join(str(arg) for arg in rsync_command)
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
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Ctrl+C pressed. Quitting PySync...")
        sys.exit(1)
