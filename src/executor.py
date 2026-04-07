import subprocess

from logger import logger


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
