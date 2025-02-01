import os
from typing import List
from dataclasses import dataclass
import logging
import asyncio

import FreeSimpleGUI as sg

from auto_slicer.util import get_config_parameter, set_config_parameter
from auto_slicer.octopi_integration import pre_heat, initialize_client, is_print_job_active


logger = logging.getLogger(__name__)


@dataclass
class BoMLineItem:
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


DEFAULT_TEXT_SETTINGS = {
    'font': ('Helvetica', 16),
}


async def create_stl_file_selection_ui() -> str | None:
    """
    Create a GUI to allow the user to select a file or folder.

    Returns:
        str: The selected file or folder path.
    """

    layout = [
        [
            sg.Text("Octopi print job is currently running:"),
            sg.Text(str(await is_print_job_active()).upper(), key='-STATUS-', size=(20, 1))],
        [sg.Button('Preheat Printer', key='-PREHEAT-')],
        [sg.Text("Octopi URL:"), sg.InputText(get_config_parameter("url"), key='-URL-'), sg.Button("Update url")],
        [sg.Text("Select a STEP, STP, or STL file, or a folder containing STEP, STP, or STL files:")],
        [
            sg.Input(key='-FILE-', enable_events=True),
            sg.FileBrowse("Browse Files", file_types=(
                ("STL Files", "*.stl"),
                ("STEP Files", "*.step"),
                ("STP Files", "*.stp"))),
        ],
        [sg.Text("OR")],
        [
            sg.Input(key='-FOLDER-', enable_events=True),
            sg.FolderBrowse("Browse Folders"),
        ],
        [sg.Button('OK'), sg.Button('Cancel')]
    ]

    window = sg.Window('File/Folder Selection', layout, finalize=True)
    asyncio.create_task(initialize_client())

    async def update_printer_status():
        while True:
            try:
                status = await is_print_job_active()
                window['-STATUS-'].update(str(status).upper())
            except Exception as e:
                window['-STATUS-'].update(f'Error: {e}')
            await asyncio.sleep(10)

    status_update_task = asyncio.create_task(update_printer_status())

    async def event_handler(event, values) -> str | None:
        if event == 'OK':
            file_path = values['-FILE-']
            folder_path = values['-FOLDER-']
            if file_path and os.path.exists(file_path):
                window.close()
                return file_path
            elif folder_path and os.path.exists(folder_path):
                window.close()
                return folder_path
            else:
                sg.popup_error('Please select a valid file or folder.')
        elif event == '-PREHEAT-':
            try:
                await pre_heat()
                sg.popup('Printer is preheating!')
            except Exception as e:
                sg.popup_error(f'Failed to preheat printer: {e}')
        elif event == 'Update url':
            url = values['-URL-']
            set_config_parameter("url", url)
            logger.info("Set URL to %s", url)
            asyncio.create_task(initialize_client())

    async def event_loop():
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, 'Cancel'):
                logger.info("User cancelled or closed the window.")
                break
            result = await event_handler(event, values)
            await asyncio.sleep(0.01)
            if result:
                status_update_task.cancel()
                window.close()
                return result

    return await event_loop()


def create_part_selection_ui(
        parts_list: List[BoMLineItem]) -> List[BoMLineItem]:
    """
    Create a GUI to display parts with checkboxes and editable quantities, allowing selection for processing.

    Args:
        parts_list (List[BoMLineItem]): A list of tuples representing parts and their quantities.

    Returns:
        List[BoMLineItem]: A list of tuples representing the selected parts and their quantities.
    """
    logger.debug("Parts list: %s", parts_list)
    layout = [
        [
            sg.Checkbox('', default=True, key=f'CHECK_{index}', size=(20, 1)),
            sg.Text(f'Part: {bom_item.part_name}', **DEFAULT_TEXT_SETTINGS),
            sg.InputText(
                default_text=str(bom_item.quantity),
                key=f'QUANTITY_{index}', justification='right',
                **DEFAULT_TEXT_SETTINGS)
        ]
        for index, bom_item in enumerate(parts_list)
    ]
    layout.append([sg.Button('Select All'), sg.Button('Clear All'),
                  sg.Button('CONTINUE'), sg.Button('Cancel')])

    window = sg.Window('Select Parts for Processing', layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancel'):
            logger.info("User cancelled or closed the window.")
            break
        if event == 'Select All':
            for index in range(len(parts_list)):
                window[f'CHECK_{index}'].update(value=True)
        if event == 'Clear All':
            for index in range(len(parts_list)):
                window[f'CHECK_{index}'].update(value=False)
        if event == 'CONTINUE':
            for index, part_info in enumerate(parts_list):
                if values[f'CHECK_{index}']:
                    part_info.quantity = int(values[f'QUANTITY_{index}'])
            window.close()
            return parts_list


def create_slicer_config_selection_ui(config_options: List[str]) -> str:
    """
    Create a GUI to allow the user to select a slicer configuration from a dropdown list or set up a new configuration.

    Args:
        config_options (List[str]): A list of available slicer configuration options.

    Returns:
        str: The selected slicer configuration option.
    """
    layout = [
        [sg.Text("Select a Slicer Configuration:")],
        [sg.Combo(config_options, key='-CONFIG-', readonly=True)],
        [sg.Button('Continue'), sg.Button('Cancel')],
        [sg.Text("OR")],
        [sg.Text("Set up a new configuration:")],
        [
            sg.Input(key='-NEW_CONFIG-', enable_events=True),
            sg.FileBrowse("Browse Files", file_types=(("Config Files", "*.ini"), ("All Files", "*.*"))),
        ],
        [sg.Button('Add Config')]
    ]

    window = sg.Window('Slicer Configuration Selection', layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancel'):
            logger.debug("User cancelled or closed the window.")
            break
        elif event == 'Continue':
            config_selection = values['-CONFIG-']
            if config_selection:
                window.close()
                return config_selection
            sg.popup_error('Please select a valid configuration.')
        elif event == 'Add Config':
            new_config_path = values['-NEW_CONFIG-']
            if new_config_path and os.path.exists(new_config_path):
                slicer_profiles_folder = os.path.join(
                    os.getcwd(), 'slicer_profiles')
                if not os.path.exists(slicer_profiles_folder):
                    os.makedirs(slicer_profiles_folder)
                new_config_name = os.path.basename(new_config_path)
                destination_path = os.path.join(
                    slicer_profiles_folder, new_config_name)
                os.rename(new_config_path, destination_path)
                sg.popup(
                    'Configuration added successfully by moving the .ini file into ./slicer_profiles.')
                config_options.append(new_config_name)
                window['-CONFIG-'].update(values=config_options)
            else:
                sg.popup_error('Please select a valid file.')

    window.close()
    return None


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


def parts_data_from_file_dict(file_dict: dict) -> List[BoMLineItem]:
    """
    Extract parts data from a dictionary of files.

    Args:
        file_dict (dict): A dictionary of file paths, where the keys are the file names
        and the values are the full file paths.

    Returns:
        List[BoMLineItem]: A list of tuples representing parts, quantities, and file paths.
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
                    BoMLineItem(os.path.basename(file_path), 1, file_path)
                )
        else:
            raise ValueError(
                "Invalid file_dict format! \n{}".format(file_dict))
    return parts_data
