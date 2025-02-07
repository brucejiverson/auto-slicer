import os
from typing import List
import logging
import asyncio

import FreeSimpleGUI as sg

from auto_slicer.definitions import STLBoM, STLFile
from auto_slicer.util import get_config_parameter, set_config_parameter
from auto_slicer.octopi_integration import pre_heat, initialize_client, is_print_job_active


logger = logging.getLogger(__name__)


DEFAULT_TEXT_SETTINGS = {
    'font': ('Helvetica', 16),
}


pages_names = (
    "Select a file or folder",
    "Select parts for processing",
    "Select a slicer configuration"
)


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
        parts_list: List[STLFile]) -> STLBoM:
    """
    Create a GUI to display parts with checkboxes and editable quantities, allowing selection for processing.

    Args:
        parts_list (List[STLFile]): A list of tuples representing parts and their quantities.

    Returns:
        STLBoM: A list of tuples representing selected parts and their quantities.
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

    # get the parent folder name
    parent_folder = os.path.basename(os.path.dirname(parts_list[0].file_path))

    # create an input for the project name that defaults to the parent folder
    # name
    layout.append([sg.Text("Project Name:"), sg.InputText(
        default_text=parent_folder, key='-PROJECT_NAME-')])

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
            # drop all of the parts that were not selected
            parts_list = [part_info for index, part_info in enumerate(
                parts_list) if values[f'CHECK_{index}']]

            for index, part_info in enumerate(parts_list):
                part_info.quantity = int(values[f'QUANTITY_{index}'])
            window.close()
            return STLBoM(
                project_name=values['-PROJECT_NAME-'],
                parts=parts_list
            )


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
        [sg.Button('Add Config')],
        [sg.Checkbox('Use Continuous Print', key='-CONTINUOUS_PRINT-')],
        [sg.Checkbox('Start Print After Slicing', key='-START_AFTER-')],
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
