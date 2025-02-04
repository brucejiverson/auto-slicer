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
            template_path,
            config_path)

    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get(
            parameter,
            f"Parameter '{parameter}' not found in the config file.")


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


def clean_file_dict(file_dict) -> dict:
    """Recursively remove empty folders from a file dictionary."""

    cleaned_dict = {}
    for key, value in list(file_dict.items()):
        if isinstance(value, dict):
            cleaned_value = clean_file_dict(value)
            if cleaned_value:
                cleaned_dict[key] = cleaned_value
        elif isinstance(value, list):
            if value:
                cleaned_dict[key] = value
    return cleaned_dict


def create_dict_of_files(
        folder_path: str,
        valid_extensions: list[str]) -> dict:
    """
    Get a dictionary of files in a folder with valid file extensions organized heirarchically.

    Args:
        folder_path (str): The path to the folder containing files.
        valid_extensions (list[str]): A set of valid file extensions to screen for.

    Returns:
        dict: A dictionary of file paths, where the keys are the file names and the values are the full file paths.
    """

    root_folder = os.path.basename(folder_path)
    files = {root_folder: []}
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        is_file = os.path.isfile(item_path)
        valid_type = os.path.splitext(item)[1].lower() in valid_extensions
        if is_file and valid_type:
            file_path = os.path.join(folder_path, item)
            files[root_folder].append(file_path)

        elif os.path.isdir(item_path):
            files[item] = create_dict_of_files(item_path, valid_extensions)
    return clean_file_dict(files)
