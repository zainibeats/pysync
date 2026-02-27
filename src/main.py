import os
import subprocess
import json

# Helper functions
from helpers import is_path_ready
from logger import logger

# Backup rsync job list
with open('config.json', 'r') as file:
    data = json.load(file)
    backup_jobs = data['jobs']

# Rsync function
def run_rsync_job(job: dict) -> None:

    # Set source and destination if name matches job parameters    
    for source in data["sources"]:
        if source["name"] == job["source"]:
            src = os.path.expanduser(source["path"])
            src_mp = source.get("mount_point")
    for destination in data["destinations"]:
        if destination["name"] == job["destination"]:
            dst = os.path.expanduser(destination["path"])
            dst_mp = destination.get("mount_point")

    # Skip if source or destination is not ready
    if not is_path_ready(src, source["type"], src_mp):
        logger.warning(f"Source not ready: {src}")
        return
    if not is_path_ready(dst, destination["type"], dst_mp):
        logger.warning(f"Destination not ready: {dst}")
        return

    # Begin building rsync command
    cmd = ["rsync"] + job["flags"]
    # Add exclusion list if marked as so
    if job["exclude_from"]:
        cmd += ["--exclude-from", os.path.expanduser(job["exclude_from"])]
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


# Main for loop
def main() -> None:
    for job in backup_jobs:
        run_rsync_job(job)


if __name__ == "__main__":
    main()
