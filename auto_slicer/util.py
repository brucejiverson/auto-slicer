import json
import shutil
import os

import logging

logger = logging.getLogger(__name__)


def get_config_parameter(parameter: str) -> str:
    """Reads from config.json and returns the matching value.
    If config.json does not exist, copies config_template.json to config.json
    and warns the user to fill out the information.

    Args:
        parameter (str): The key to look up in the config file.

    Returns:
        str: The value associated with the key.
    """
    config_path = 'config.json'
    template_path = 'config_template.json'

    if not os.path.exists(config_path):
        shutil.copy(template_path, config_path)
        logger.warning(
            'config.json not found. Copied %s to %s. Please fill out the information.',
            template_path, config_path
        )

    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get(parameter, f"Parameter '{parameter}' not found in the config file.")


def set_config_parameter(parameter: str, value: str):
    """Writes to config.json.

    Args:
        parameter (str): The key to write to the config file.
        value (str): The value to write to the config file.
    """
    config_path = 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        data[parameter] = value

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        logger.info("Wrote %s to %s.", value, parameter)