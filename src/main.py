# main.py

import os
import subprocess

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Helper functions
from helpers import is_path_ready
from logger import logger

# Backup rsync job list
backup_jobs = [
    # test backup
    {
        "name": "Test backup",
        "source": os.getenv("TEST_SOURCE"),
        "dest": os.getenv("TEST_DEST"),
        "exclude-from": None,
        "flags": ["-av", "--delete"],
    },
]

# Rsync function
def run_rsync_job(job: dict) -> None:
    # Set source and destination variables
    src = job["source"]
    dst = job["dest"]

    # Skip if source or destination is not ready
    if not is_path_ready(src):
        logger.warning(f"Source not ready: {src}")
        return
    if not is_path_ready(dst):
        logger.warning(f"Destination not ready: {dst}")
        return

    # Begin building rsync command
    cmd = ["rsync"] + job["flags"]
    # Add exclusion list if marked as so
    if job["exclude-from"]:
        cmd += ["--exclude-from", job["exclude-from"]]
    # Add source and destination
    cmd += [src, dst]

    # Logs upcoming rsync command
    logger.info(f"Running rsync: {' '.join(cmd)}")
    try:
        # Execute the rsync command, capturing output and raising on error
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        # Log success and any stdout returned by rsync
        logger.info(f"Job {job['name']} succeeded!. {result.stdout}")
    except subprocess.CalledProcessError as exc:
        # Log failure details including exit code, stdout, and stderr
        logger.error(
            f"Job {job['name']} failed (exit {exc.returncode}):\n"
            f"stdout: {exc.stdout}\nstderr: {exc.stderr}"
        )



# Main forloop
def main() -> None:
    for job in backup_jobs:
        run_rsync_job(job)


if __name__ == "__main__":
    main()
