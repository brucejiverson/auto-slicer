import FreeSimpleGUI as sg
import os
from typing import List
from dataclasses import dataclass
import logging

import auto_slicer.octopi_integration as octopi_integration
from auto_slicer import slice_stl


logger = logging.getLogger(__name__)


@dataclass
class BoMLineItem:
    part_name: str
    quantity: int
    file_path: str


DEFAULT_TEXT_SETTINGS = {
    'font': ('Helvetica', 16),
}


def create_file_folder_ui() -> str:
    """
    Create a GUI to allow the user to select a file or folder.

    Returns:
        str: The selected file or folder path.
    """

    layout = [
        [sg.Checkbox('Preheat Printer Immediately', default=True, key='-PREHEAT-')],
        [sg.Text("Select a STEP, STP, or STL file, or a folder containing STEP, STP, or STL files:")],
        [
            sg.Input(key='-FILE-', enable_events=True),
            sg.FileBrowse("Browse Files", file_types=(
                ("STEP Files", "*.step"),
                ("STP Files", "*.stp"),
                ("STL Files", "*.stl"))),
            ],
        [sg.Text("OR")],
        [
            sg.Input(key='-FOLDER-', enable_events=True),
            sg.FolderBrowse("Browse Folders"),
        ],
        [sg.Button('OK'), sg.Button('Cancel')]
    ]

    window = sg.Window('File/Folder Selection', layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancel'):
            logger.info("User cancelled or closed the window.")
            break
        elif event == 'OK':
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
            # get the value of the checkbox
            should_preheat = values['-PREHEAT-']

    window.close()
    return None


def create_parts_ui(parts_list: List[BoMLineItem]) -> List[BoMLineItem]:
    """
    Create a GUI to display parts with checkboxes and editable quantities, allowing selection for processing.

    Args:
        parts_list (List[BoMLineItem]): A list of tuples representing parts and their quantities.

    Returns:
        List[BoMLineItem]: A list of tuples representing the selected parts and their quantities.
    """
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
    layout.append([sg.Button('Select All'), sg.Button('Clear All'), sg.Button('SLICE'), sg.Button('Cancel')])

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
        if event == 'SLICE':
            for index, part_info in enumerate(parts_list):
                if values[f'CHECK_{index}']:
                    part_info.quantity = int(values[f'QUANTITY_{index}'])
            window.close()
            return parts_list


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


def create_dict_of_files(folder_path: str, valid_extensions: list[str]) -> dict:
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
    # here value will either be another dict representing a subfolder or a list of file paths
    for folder_name, value in file_dict.items():
        if isinstance(value, dict):
            parts_data.extend(parts_data_from_file_dict(value))
        elif isinstance(value, list):
            for file_path in value:
                parts_data.append(
                    BoMLineItem(os.path.basename(file_path), 1, file_path)
                )
        else:
            raise ValueError("Invalid file_dict format! \n{}".format(file_dict))
    return parts_data


def main():
    input_path = create_file_folder_ui()
    if input_path:
        if os.path.isfile(input_path):
            parts_data = [(os.path.basename(input_path), 1)]
        else:
            # Logic for processing a folder
            file_dict = create_dict_of_files(input_path, ['.step', '.stp', '.stl'])
            parts_data = parts_data_from_file_dict(file_dict)

        logger.debug("File dict:", file_dict)
        logger.debug("Parts data:", parts_data)
        mutated_parts_data = create_parts_ui(parts_data)
        logger.debug("Mutated parts data:", mutated_parts_data)
        # Slice each part
        outputs = []
        for bom_item in mutated_parts_data:
            logger.info(f'Slicing {bom_item.part_name}.')
            # Logic for slicing the part
            output = slice_stl.slice_stl_brute_force_rotation_no_support(bom_item.file_path)
            outputs.append(output)

        logger.info(f"Outputs: {outputs}")
        # Upload each part to a cloud service
        gcode_file_dict = create_dict_of_files(input_path, ['.gcode'])
        response = octopi_integration.upload_nested_dict_to_octopi(gcode_file_dict)
        logger.info(f"Upload response: {response}")


if __name__ == "__main__":
    main()
