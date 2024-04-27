import requests
import json
from octorest import OctoRest


def get_api_key() -> str:
    """Reads from config.json and returns the api key

    Returns:
        str: The api key
    """
    with open('config.json', 'r') as f:
        data = json.load(f)
        return data['octoprint_api_key']


#  OCTOPI REFERENCE! https://docs.octoprint.org/en/master/api/files.html


def upload_nested_dict_to_octopi(gcode_dict: dict, parent_folders: str = ""):
    """
    Recursively uploads gcode files to OctoPrint.

    Args:
        gcode_dict (dict): A dictionary of gcode files, where the keys are the file names
            and the values are the full file paths.
    """

    client = OctoRest(url="http://octopi.local", apikey=get_api_key())

    for folder_name, value in gcode_dict.items():
        # create the folder
        print(f'creating folder {parent_folders + folder_name}')
        response = client.new_folder(parent_folders + folder_name)

        if isinstance(value, dict):
            # create a folder
            response = client.new_folder(folder_name)
            print("Folder creation successful:", response)
            upload_nested_dict_to_octopi(value, f'{parent_folders}/{folder_name}/')
        elif isinstance(value, list):
            # location – The target location to which to upload the file. Currently only local and sdcard are supported
            # here, with local referring to OctoPrint’s uploads folder and sdcard referring to the printer’s SD card.
            # If an upload targets the SD card, it will also be stored locally first.
            # path – The path within the location to upload the file to or create the folder in (without the future
            # filename
            # or foldername - basically the parent folder). If unset will be taken from the provided file’s name or
            # foldername and default to the root folder of the location.

            for file_path in value:
                print(f'uploading {file_path} to {parent_folders}')
                client.upload(file_path, path=parent_folders, location="local")
        else:
            raise ValueError("Invalid gcode_dict format! \n{}".format(gcode_dict))


# REFERENCE FOR CONTINUOUS PRINT
# https://github.com/smartin015/continuousprint/blob/master/api_examples/example.py
# def set_active(active=True):
#     return requests.post(
#         f"https://octopi.local/plugin/continuousprint/set_active",
#         headers={"X-Api-Key": get_api_key()},
#         data={"active": active},
#     ).json()


def add_set_to_continous_print(path, sd=False, count=1, jobName="Job", jobDraft=True):
    return requests.post(
        "https://octopi.local/plugin/continuousprint/set/add",
        headers={"X-Api-Key": get_api_key()},
        data=dict(
            path=path,
            sd=sd,
            count=count,
            jobName=jobName,
            jobDraft=jobDraft,
        ),
    ).json()


def get_continuous_print_state():
    return requests.get(
        "https://octopi.local/plugin/continuousprint/state/get",
        headers={"X-Api-Key": get_api_key()},
    ).json()


if __name__ == "__main__":
    print(get_continuous_print_state())
