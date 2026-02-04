# main.py

import os
import subprocess

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Helper functions
from src.helpers import is_path_ready
from src.logging import logger

# Backup rsync job list
backup_jobs = [
    # Cryptomator backup
    {
        "name": "Cryptomator backup",
        "source": os.getenv("CRYPTOMATOR_SOURCE"),
        "dest": os.getenv("SYNCTHING_DESKTOP_DIR"),
        "exclude-from": None,
        "flags": ["-av", "--delete"],
    },
    # Dropbox backup
    {
        "name": "Dropbox backup",
        "source": os.getenv("DROPBOX_SOURCE"),
        "dest": os.getenv("SYNCTHING_DESKTOP_DIR"),
        "exclude-from": os.getenv("RSYNC_EXCLUDES_FILE"),
        "flags": ["-av", "--delete"],
    },
    # Ubuntu server home directory backup
    {
        "name": "Ubuntu home",
        "source": os.getenv("UBUNTU_HOME_SOURCE"),
        "dest": os.path.join(os.getenv("SYNCTHING_UBUNTU_DIR"), "home"),
        "exclude-from": os.getenv("RSYNC_EXCLUDES_FILE"),
        "flags": ["-av", "--delete"],
    },
]


# Main loop
def main() -> None:
    for job in backup_jobs:
        run_rsync_job(job)


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


if __name__ == "__main__":
    main()
