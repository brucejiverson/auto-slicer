from dataclasses import dataclass
import json
import shutil
import os
import logging


logger = logging.getLogger(__name__)


@dataclass
class STLFile:
    """
    Represents a Bill of Materials (BoM) line item.

    Attributes:
        part_name (str): The name of the part.
        quantity (int): The quantity of the part.
        file_path (str): The file path associated with the part.
        slice_warnings (str): Any warnings generated during the slicing process.
        gcode_path (str): The G-code file path associated with the part.
    """
    part_name: str
    quantity: int
    file_path: str
    slice_warnings: str = None
    gcode_path: str = None


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


def parts_data_from_file_dict(file_dict: dict) -> list[STLFile]:
    """
    Extract parts data from a dictionary of files.

    Args:
        file_dict (dict): A dictionary of file paths, where the keys are the file names
        and the values are the full file paths.

    Returns:
        List[STLFile]: A list of tuples representing parts, quantities, and file paths.
    """

    parts_data = []
    # here value will either be another dict representing a subfolder or a
    # list of file paths
    for folder_name, value in file_dict.items():
        if isinstance(value, dict):
            parts_data.extend(parts_data_from_file_dict(value))
        elif isinstance(value, list):
            for file_path in value:
                parts_data.append(
                    STLFile(os.path.basename(file_path), 1, file_path)
                )
        else:
            raise ValueError(
                "Invalid file_dict format! \n{}".format(file_dict))
    return parts_data
