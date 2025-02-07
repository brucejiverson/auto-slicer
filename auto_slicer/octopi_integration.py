import logging
import json
import requests
import time
from datetime import datetime
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
    files = client.files(location=path, recursive=True)[
        'files']   # this returns a list of dictionaries
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


def upload_file(
        file,
        *,
        location='local',
        select=False,
        userdata=None,
        path=None):
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
        logger.info(
            "Creating project folder: %s",
            bill_of_materials.project_name)
        response = create_folder(bill_of_materials.project_name)
        if not response["done"]:
            raise RuntimeError(
                f"Failed to create project folder: {
                    bill_of_materials.project_name}")

    for part in bill_of_materials.parts:
        logger.info(
            'Uploading %s to folder %s',
            part.gcode_path,
            bill_of_materials.project_name)
        response = upload_file(
            part.gcode_path,
            path=bill_of_materials.project_name)
        if not response["done"]:
            raise RuntimeError(
                f"Failed to upload {
                    part.gcode_path} to {
                    bill_of_materials.project_name}")
        else:
            logger.info("Upload successful for %s", part.gcode_path)


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

    full_url = f"{host_url}/plugin/continuousprint/state/get"
    logger.info("State check - Full URL: %s", full_url)  # Debug full URL

    req = requests.get(
        full_url,
        headers={"X-Api-Key": get_api_key()},
        timeout=timeout
    ).json()
    logger.debug("Continuous print state: %s", req)
    logger.info("Continuous print state: %s", req['status'])
    """Example response:
    {'active': False, 'profile': 'Generic', 'status': 'Inactive (click Start Managing)', 'statusType': 'NORMAL', 'queues': [{'name': 'local', 'strategy': 'IN_ORDER', 'jobs': [{'queue': 'local', 'name': 'Job 1', 'count': 1, 'draft': False, 'sets': [{'path': 'Hour clock 6 mm nozzle/hour_rotor_2h11m_0.20mm_210C_PLA_ENDER3BLTOUCH.gcode', 'count': 1, 'metadata': '{"estimatedPrintTime":9327.111602476372,"filamentLengths":[9698.619369531516]}', 'materials': [], 'profiles': [], 'id': 73, 'rank': 0.0, 'sd': False, 'remaining': 0, 'completed': 1, 'missing_file': True}, {'path': 'Hour clock 6 mm nozzle/rotor_cover_1h0m_0.20mm_210C_PLA_ENDER3BLTOUCH.gcode', 'count': 1, 'metadata':
'{"estimatedPrintTime":4968.768529952111,"filamentLengths":[5142.755256652948]}', 'materials': [], 'profiles': [], 'id': 74, 'rank': 1.0, 'sd': False, 'remaining': 0, 'completed': 1, 'missing_file': True}, {'path': 'Hour clock 6 mm nozzle/min_rotor_1h16m_0.20mm_210C_PLA_ENDER3BLTOUCH.gcode', 'count': 1, 'metadata': '{"estimatedPrintTime":5613.150037247091,"filamentLengths":[5998.090835633688]}', 'materials': [], 'profiles': [], 'id': 75, 'rank': 2.0, 'sd': False, 'remaining': 1, 'completed': 0, 'missing_file': True}, {'path': 'Hour clock 6 mm nozzle/rear_cover_tics_49m_0.20mm_210C_PLA_ENDER3BLTOUCH.gcode', 'count': 1, 'metadata': '{"estimatedPrintTime":3899.5899984155794,"filamentLengths":[4167.450698778499]}', 'materials': [], 'profiles': [], 'id': 76, 'rank': 3.0, 'sd': False, 'remaining': 1, 'completed': 0, 'missing_file': True}], 'created': 1738518153, 'id': 30, 'remaining': 1, 'acquired': False}], 'active_set': None, 'addr': None, 'peers': [], 'rank': 0.0}]}
    """
    return req


def create_job(name: str, timeout=10):
    """Creates a new continuous print job"""
    host_url = get_url()

    req = requests.post(
        f"{host_url}/plugin/continuousprint/job/add",
        headers={"X-Api-Key": get_api_key()},
        data={"json": json.dumps({"name": name})},
        timeout=timeout
    )

    req.raise_for_status()
    return req.json()


def add_set_to_continous_print(
        path: str,
        job_name: str,  # Add job_name parameter
        job_id: int | None = None,
        sd=False,
        count=1,
        job_draft=True,
        timeout=10):
    """
    Adds a set to the continuous print queue in OctoPrint.

    Args:
        path (str): The path to the file to be added to the print queue.
        job_name (str): The name of the job to be added.
        job_id (int | None, optional): The ID of the job, if available. Defaults to None.
        sd (bool, optional): Whether the file is on the SD card. Defaults to False.
        count (int, optional): The number of times to print the set. Defaults to 1.
        job_draft (bool, optional): Whether the job is a draft. Defaults to True.
        timeout (int, optional): The timeout for the request in seconds. Defaults to 10.

    Returns:
        dict: The JSON response from the OctoPrint API.

    Raises:
        requests.exceptions.RequestException: If the request fails.
    """
    host_url = get_url()
    logger.info("Adding set to continuous print: %s", path)

    req = requests.post(
        f"{host_url}/plugin/continuousprint/set/add",
        headers={"X-Api-Key": get_api_key()},
        data={
            "path": path,
            "sd": sd,
            "count": count,
            "jobName": job_name,
            "job": job_id,
            "jobDraft": job_draft,
        },
        timeout=timeout
    )

    try:
        req.raise_for_status()
        logger.debug("Add set response: %s", req.json())
        return req.json()
    except requests.exceptions.RequestException as e:
        logger.error("Failed to add set: %s", str(e))
        logger.error(
            "Response content: %s",
            req.text if hasattr(
                req,
                'text') else 'No response text')
        raise e


async def create_and_configure_continuous_print_job(bill_of_materials: STLBoM):
    """
    Creates and configures a continuous print job in OctoPi.
    This function first creates a print job using the provided bill of materials (BoM).
    It then adds each part from the BoM to the created job, configuring each part as a draft if there are multiple parts.
    Args:
        bill_of_materials (STLBoM): An object containing the project name and a list of parts to be printed.
                                    Each part should have a 'gcode_path' attribute.
    Returns:
        None
    """

    # First create the job
    # job = create_job(bill_of_materials.project_name)
    # job_name = job['id']  # Get the job ID from the response
    job_name = bill_of_materials.project_name + " " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    job_id: int = None
    # Then add sets to that job
    n_parts = len(bill_of_materials.parts)
    for part in bill_of_materials.parts:
        time.sleep(0.5)
        octopi_path = f'{bill_of_materials.project_name}/{part.part_name}.gcode'
        draft = True if n_parts > 1 else False
        print(part)
        response = add_set_to_continous_print(
            octopi_path, job_name, job_id=job_id, job_draft=draft)
        job_id = response['job_id']  # Get the job ID from the response

    logger.info("Continuous print job created and configured.")


def set_active(active: bool = True, timeout: int = 10) -> dict:
    """
    Set the active state of the continuous print plugin.

    Args:
        active (bool, optional): Whether to activate or deactivate the plugin. Defaults to True.
        timeout (int, optional): The maximum time to wait for a response from the server. Defaults to 10 seconds.

    Returns:
        dict: The JSON response from the server.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the network request.
    """
    state = get_continuous_print_state()
    if state['active'] == active:
        logger.info("Continuous print active state already set to: %s", active)
        return state

    host_url = get_url()
    logger.info("Setting continuous print active state to: %s", active)
    req = requests.post(
        f"{host_url}/plugin/continuousprint/set_active",
        headers={"X-Api-Key": get_api_key()},
        data={"active": active},
        timeout=timeout
    ).json()
    logger.debug("Set active response: %s", req)
    return req
