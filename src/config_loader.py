import json
import os

from logger import logger


def load_config() -> dict | None:
    config_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "config.json"
    )
    try:
        with open(config_file, "r") as file:
            config = json.load(file)
            return config
    except FileNotFoundError:
        logger.error(
            "Config file not found. Make sure a config.json exists in the pysync directory."
        )
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Config.json is malformed!\nError message:\n{e}")
        return None
