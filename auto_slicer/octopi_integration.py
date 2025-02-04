import logging
import requests

from octorest import OctoRest

from auto_slicer.definitions import STLBoM, RemoteFile, RemoteObjectTypes
from auto_slicer.util import get_config_parameter

logger = logging.getLogger(__name__)


#  OCTOPI REFERENCE! https://docs.octoprint.org/en/master/api/files.html
# https://docs.octoprint.org/en/master/api/files.html#upload-file-or-create-folder
# example script
# https://github.com/dougbrion/OctoRest/blob/master/examples/basic/basic.py


# BASIC FUNCTIONS
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


client: OctoRest | None = None


async def initialize_client() -> OctoRest:
    """
    Initialize the OctoRest client.

    Returns:
        None
    """
    global client
    if client is None:
        try:
            logger.info("Initializing OctoRest client.")
            client = OctoRest(url=get_url(), apikey=get_api_key())
            logger.info("OctoRest client initialized and connected.")
            return client
        except Exception as e:
            logger.error("Failed to initialize OctoRest client.")
            raise e
    else:
        logger.debug("OctoRest client already initialized.")
        return client


# RETRIEVING INFORMATION
async def is_print_job_active() -> bool:
    """
    Check if a print job is currently active.

    Returns:
        bool: True if a print job is active, False otherwise.
    """
    global client
    if client is None:
        await initialize_client()

    return client.printer()['state']['flags']['printing']


async def get_printer_info() -> dict:
    """
    Get the information of the printer.

    Returns:
        dict: The JSON response from the OctoPrint server.
    """
    global client
    if client is None:
        await initialize_client()

    message = ""
    message += str(client.version) + "\n"
    message += str(client.job_info()) + "\n"
    printing = client.printer()['state']['flags']['printing']
    if printing:
        message += "Currently printing!\n"
    else:
        message += "Not currently printing...\n"
    logger.info(message)
    return message


def octorest_dict_to_file_object(file_dict: dict) -> RemoteFile:
    """
    Convert an OctoRest dictionary to a RemoteFile object.

    Args:
        file_dict (dict): The dictionary to convert.

    Returns:
        RemoteFile: The converted RemoteFile object.
    """
    return RemoteFile(
        name=file_dict.get('name'),
        date=file_dict.get('date'),
        display=file_dict.get('display'),
        gcodeAnalysis=file_dict.get('gcodeAnalysis'),
        hash=file_dict.get('hash'),
        origin=file_dict.get('origin'),
        path=file_dict.get('path'),
        prints=file_dict.get('prints'),
        refs=file_dict.get('refs'),
        size=file_dict.get('size'),
        statistics=file_dict.get('statistics'),
        type=RemoteObjectTypes.FOLDER if file_dict.get('type') == 'folder' else RemoteObjectTypes.FILE,
    )


async def get_files_and_folders(path: str = "") -> list[RemoteFile]:
    """
    Get the files on the OctoPrint server.

    Args:
        path (str, optional): The path to retrieve files from. Defaults to "".
        recursive (bool, optional): Whether to retrieve files recursively. Defaults to False.

    Returns:
        list[RemoteFile]: A list of RemoteFile objects.
    """

    global client
    if client is None:
        await initialize_client()
    logger.debug("Retrieving files from OctoPrint server for path %s", path)
    files = client.files(location=path, recursive=True)['files']   # this returns a list of dictionaries
    # drop every progress key
    for file in files:
        for item in ('gcodeAnalysis', 'statistics', 'prints', 'progress'):
            if item in file:
                del file[item]

    remote_files: list[RemoteFile] = []
    for file in files:
        remote_files.append(octorest_dict_to_file_object(file))
        # if remote_files[-1].type == RemoteObjectTypes.FOLDER:
        #     remote_files[-1].children = await get_files(remote_files[-1].path)
        # print(remote_files[-1].name)
        # print(remote_files[-1].type)
        # print(file.get('children'))
        logger.debug("Retrieved object: %s", remote_files[-1].name)
    return remote_files


async def pre_heat(tool_target: int = 150, bed_target: int = 45) -> None:
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

    global client
    if client is None:
        await initialize_client()

    if not await is_print_job_active():
        client.tool_target(tool_target)
        client.bed_target(bed_target)
    else:
        logger.error("Cannot preheat while a print job is active.")
        raise RuntimeError("Cannot preheat while a print job is active.")


def create_folder(folder_name, path=None, location='local'):
    """Create a new folder on OctoPrint's file system
    Note: Folder creation is only supported on the local file system.
    """
    files = {
        'foldername': (None, folder_name),
    }
    if path:
        files['path'] = (None, path)

    return client._post('/api/files/{}'.format(location), files=files)


def upload_file(file, *, location='local', select=False, userdata=None, path=None):
    """Upload a file to OctoPrint. Made this in order to get files to actually go into folders.
    Args:
        file: Path to file or tuple of (filename, file-like object)
        location: 'local' or 'sdcard'
        select: Whether to select file after upload
        userdata: Optional metadata to store with file
        path: Target folder path (must end with forward slash)
    """

    global client

    with client._file_tuple(file) as file_tuple:
        files = {
            'file': file_tuple,
            'select': (None, str(select).lower()),
            'print': (None, str(print).lower())
        }
        if userdata:
            files['userdata'] = (None, userdata)
        if path:
            if not path.endswith('/'):
                path += '/'
            files['path'] = (None, path)
        return client._post('/api/files/{}'.format(location), files=files)


async def upload_files_to_octopi(bill_of_materials: STLBoM):
    """
    Uploads a list of gcode files to OctoPrint under a specified project folder.

    Args:
        bill_of_materials (STLBoM): The bill of materials containing the project name and file list.
    """

    logger.info("Uploading gcode files to OctoPrint.")
    logger.debug("Bill of materials:\n%s", bill_of_materials)
    global client
    if client is None:
        await initialize_client()

    # create the project folder
    if bill_of_materials.project_name not in [file.name for file in await get_files_and_folders()]:
        logger.info("Creating project folder: %s", bill_of_materials.project_name)
        response = create_folder(bill_of_materials.project_name)
        if not response["done"]:
            raise RuntimeError(f"Failed to create project folder: {bill_of_materials.project_name}")

    for part in bill_of_materials.parts:
        logger.info('Uploading %s to folder %s', part.gcode_path, bill_of_materials.project_name)
        response = upload_file(part.gcode_path, path=bill_of_materials.project_name)
        if not response["done"]:
            raise RuntimeError(f"Failed to upload {part.gcode_path} to {bill_of_materials.project_name}")
        else:
            logger.info("Upload successful for %s", part.gcode_path)


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
