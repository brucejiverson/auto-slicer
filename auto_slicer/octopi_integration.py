import logging
import requests
from octorest import OctoRest
from auto_slicer.util import get_config_parameter

logger = logging.getLogger(__name__)


def get_api_key() -> str:
    """
    Retrieve the OctoPrint API key from the configuration.

    Returns:
        str: The OctoPrint API key.
    """
    return get_config_parameter("octoprint_api_key")


def get_url() -> str:
    """
    Retrieve the URL from the configuration parameters.

    Returns:
        str: The URL as a string.
    """
    return get_config_parameter("url")


#  OCTOPI REFERENCE! https://docs.octoprint.org/en/master/api/files.html
# https://docs.octoprint.org/en/master/api/files.html#upload-file-or-create-folder

def pre_heat(tool_target: int = 150, bed_target: int = 45) -> None:
    """
    Preheat the 3D printer to the specified tool and bed temperatures.

    Args:
        tool_target (int): The target temperature for the tool (extruder) in degrees Celsius. Default is 150.
        bed_target (int): The target temperature for the bed in degrees Celsius. Default is 45.

    Returns:
        None

    Raises:
        requests.exceptions.RequestException: If there is an issue with the network request.
    """
    logger.info('Preheating to %dC and %dC', tool_target, bed_target)
    client = OctoRest(url=get_url(), apikey=get_api_key())
    client.tool_target(tool_target)
    client.bed_target(bed_target)


def upload_nested_dict_to_octopi(gcode_dict: dict, parent_folders: str = ""):
    """
    Recursively uploads gcode files to OctoPrint.

    Args:
        gcode_dict (dict): A dictionary of gcode files, where the keys are the file names
            and the values are the full file paths.
        parent_folders (str, optional): The parent folder path. Defaults to "".

    Returns:
        bool: True if upload is successful, False otherwise.
    """
    logger.info("Uploading gcode files to OctoPrint.")
    client = OctoRest(url=get_url(), apikey=get_api_key())

    for folder_name, value in gcode_dict.items():
        folder_path_from_parent = parent_folders + folder_name
        # create the folder
        if parent_folders != "" and folder_name != "delete":
            print(f'creating folder {folder_path_from_parent}')
            response = client.new_folder(folder_path_from_parent)

        if isinstance(value, dict):
            # create a folder
            response = client.new_folder(folder_name)
            print("Folder creation successful:", response)
            upload_nested_dict_to_octopi(
                value, f'{parent_folders}/{folder_name}/')
        elif isinstance(value, list):
            for file_path in value:
                print(f'uploading {file_path} to {folder_path_from_parent}')
                result = client.upload(
                    file_path,
                    path=folder_path_from_parent,
                    location="local")
                if not result["done"]:
                    raise RuntimeError(
                        f"Failed to upload {file_path} to {folder_path_from_parent}")
                else:
                    logger.info("Upload successful for %s", file_path)
        else:
            raise ValueError(
                "Invalid gcode_dict format! \n{}".format(gcode_dict))


def add_set_to_continous_print(
        path,
        sd=False,
        count=1,
        jobName="Job",
        jobDraft=True,
        timeout=10):
    """
    Adds a set to the continuous print queue in OctoPrint.

    Args:
        path (str): The path to the file to be added to the print queue.
        sd (bool, optional): Whether the file is on the SD card. Defaults to False.
        count (int, optional): The number of times to print the file. Defaults to 1.
        jobName (str, optional): The name of the print job. Defaults to "Job".
        jobDraft (bool, optional): Whether the job is a draft. Defaults to True.
        timeout (int, optional): The timeout for the request in seconds. Defaults to 10.

    Returns:
        dict: The JSON response from the OctoPrint server.
    """
    host_url = get_url()
    return requests.post(
        host_url + "/plugin/continuousprint/set/add",
        headers={"X-Api-Key": get_api_key()},
        data=dict(
            path=path,
            sd=sd,
            count=count,
            jobName=jobName,
            jobDraft=jobDraft,
        ),
        timeout=timeout
    ).json()


def get_continuous_print_state(timeout=10):
    """
    Fetches the continuous print state from the OctoPrint server.

    Args:
        timeout (int, optional): The maximum time to wait for a response from the server. Defaults to 10 seconds.

    Returns:
        dict: The JSON response from the server containing the continuous print state.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the network request.
    """
    host_url = get_url()
    return requests.get(
        host_url + "/plugin/continuousprint/state/get",
        headers={"X-Api-Key": get_api_key()},
        timeout=timeout
    ).json()
