import os
import sys
import subprocess
import json
import time

# Helper functions
from helpers import is_path_ready, prompt_user
from logger import logger

# Backup rsync job list
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
with open(CONFIG_FILE, 'r') as file:
    data = json.load(file)
    backup_jobs = data['jobs']

def build_rsync_command(job: dict) -> list:
    # Set source and destination if name matches job parameters
    src = dst = None
    source = destination = None
    for s in data["sources"]:
        if s["name"] == job["source"]:
            src = os.path.expanduser(s["path"])
            src_mp = s.get("mount_point")
            source = s
            break
    for d in data["destinations"]:
        if d["name"] == job["destination"]:
            dst = os.path.expanduser(d["path"])
            dst_mp = d.get("mount_point")
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
    cmd += [src, dst]
    return cmd

def build_readable_command(cmd: list) -> str:
    result = ' '.join(str(word) for word in cmd)
    hr_cmd = ''.join(result) + "\n"
    return hr_cmd

# Rsync function
def run_rsync_job(cmd: list, job: dict) -> None:
    # Logs upcoming rsync command
    print("Running rsync commands...")
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
        logger.info(f"Job {job['name']} succeeded! {result.stdout}")
    except subprocess.CalledProcessError as exc:
        # Log failure details including exit code, stdout, and stderr
        logger.error(
            f"Job {job['name']} failed (exit {exc.returncode}):\n"
            f"stdout: {exc.stdout}\nstderr: {exc.stderr}"
        )

# Main for loop
def main() -> None:

    cmd_list = []
    hr_list = ''

    for job in backup_jobs:
        cmd = build_rsync_command(job)
        cmd_list.append(cmd)
        
        hr_cmd = ''.join(build_readable_command(cmd))
        hr_list += hr_cmd

    result = prompt_user(hr_list)
    
    if result == True:
        for cmd in cmd_list:
            run_rsync_job(cmd, job)
        time.sleep(3)
        print("Syncing complete!")
        sys.exit()
    else:
        print("Quitting PySync...")
        sys.exit()


if __name__ == "__main__":
    main()
