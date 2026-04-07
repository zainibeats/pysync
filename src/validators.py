import os

from helpers import expand_path, is_path_ready
from logger import logger


def validate_config(config: dict) -> bool:
    # CHecks for 'sources' key in config.json
    sources = config.get("sources")
    if sources is None:
        logger.error("Missing 'sources' key in config.json!")
        return False
    else:
        for source in sources:
            name = source.get("name")
            if name is None:
                logger.error(f"Missing 'name' key for source {source} in config.json!")
                return False
            path = source.get("path")
            if path is None:
                logger.error(f"Missing 'path' key for source {name} in config.json!")
                return False
            filesystem = source.get("filesystem")
            if filesystem is None:
                logger.error(
                    f"Missing 'filesystem' key for source {name} in config.json!"
                )
                return False
            if "mount_point" not in source:
                logger.error(
                    f"Missing 'mount_point' key for source {name} in config.json!"
                )
                return False
            else:
                if filesystem == "nfs":
                    mount_point = source["mount_point"]
                    if mount_point is None:
                        logger.error(
                            f"Missing 'mount_point' key for nfs source {name} in config.json! NFS shares must have a defined mount point."
                        )
                        return False

    # Checks for 'destinations' key in config.json
    destinations = config.get("destinations")
    if destinations is None:
        logger.error("Missing 'destinations' key in config.json!")
        return False
    else:
        for destination in destinations:
            name = destination.get("name")
            if name is None:
                logger.error(
                    f"Missing 'name' key for destination {destination} in config.json!"
                )
                return False
            path = destination.get("path")
            if path is None:
                logger.error(
                    f"Missing 'path' key for destination {name} in config.json!"
                )
                return False
            filesystem = destination.get("filesystem")
            if filesystem is None:
                logger.error(
                    f"Missing 'filesystem' key for destination {name} in config.json!"
                )
                return False
            if "mount_point" not in destination:
                logger.error(
                    f"Missing 'mount_point' key for destination {name} in config.json!"
                )
                return False
            else:
                if filesystem == "nfs":
                    mount_point = destination["mount_point"]
                    if mount_point is None:
                        logger.error(
                            f"Missing 'mount_point' key for nfs destination {name} in config.json! NFS shares must have a defined mount point."
                        )
                        return False

    # Checks for 'jobs' key in config.json
    jobs = config.get("jobs")
    if jobs is None:
        logger.error("Missing 'jobs' key in config.json!")
        return False
    else:
        for job in jobs:
            name = job.get("name")
            if name is None:
                logger.error(f"Missing 'name' key for job {job} in config.json!")
                return False
            source = job.get("source")
            if source is None:
                logger.error(f"Missing 'source' key for job {name} in config.json!")
                return False
            destination = job.get("destination")
            if destination is None:
                logger.error(
                    f"Missing 'destination' key for job {name} in config.json!"
                )
                return False
            if "flags" not in job:
                logger.error(f"Missing 'flags' key for job {name} in config.json!")
                return False
            if "exclude_from" not in job:
                logger.error(
                    f"Missing 'exclude_from' key for job {name} in config.json!"
                )
                return False
            else:
                # Exclude from path exists but NOT null
                if job["exclude_from"]:
                    exclude_from_file_path = expand_path(job["exclude_from"])
                    if not os.path.isfile(exclude_from_file_path):
                        logger.error(
                            f"Cannot find or read 'exclude_from' file for job {name} in config.json!"
                        )
                        return False

    return True


def validate_rsync_command(job: dict, resolved_paths: dict) -> bool:
    if not is_path_ready(
        resolved_paths["src_path"],
        resolved_paths["src_config"]["filesystem"],
        resolved_paths["src_mp"],
    ):
        logger.warning(f"Source not ready: {resolved_paths['src_path']}")
        return False
    elif not is_path_ready(
        resolved_paths["dst_path"],
        resolved_paths["dst_config"]["filesystem"],
        resolved_paths["dst_mp"],
    ):
        logger.warning(f"Destination not ready: {resolved_paths['dst_path']}")
        return False
    # Checks if '--delete' flag is to be ran on an empty source
    elif "--delete" in job["flags"]:
        try:
            list_src_dir = os.listdir(resolved_paths["src_path"])
            if not list_src_dir:
                logger.error(
                    f"Ignoring Job '{job['name']}' because the '--delete' flag is being ran on an empty source directory: {resolved_paths['src_path']}"
                )
                return False
            else:
                return True
        except (FileNotFoundError, PermissionError) as e:
            logger.error(
                f"Ignoring Job '{job['name']}' because the '--delete' flag is being ran on a source directory that cannot be read. Check permissions and verify {resolved_paths['src_path']} exists"
            )
            return False
    else:
        return True
