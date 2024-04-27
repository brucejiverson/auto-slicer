import PySimpleGUI as sg
import os
from typing import List, Tuple

import auto_slicer.octopi_integration as octopi_integration


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
            print("User cancelled or closed the window.")
            break
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

    window.close()
    return None


def create_parts_ui(parts_list: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
    """
    Create a GUI to display parts with checkboxes and editable quantities, allowing selection for processing.

    Args:
        parts_list (List[Tuple[str, int]]): A list of tuples representing parts and their quantities.

    Returns:
        List[Tuple[str, int]]: A list of tuples representing the selected parts and their quantities.
    """
    layout = [
        [
            sg.Checkbox('', default=True, key=f'CHECK_{index}', size=(20, 1)),
            sg.Text(f'Part: {part[0]}', **DEFAULT_TEXT_SETTINGS),
            sg.InputText(
                default_text=str(part[1]),
                key=f'QUANTITY_{index}', justification='right',
                **DEFAULT_TEXT_SETTINGS)
        ]
        for index, part in enumerate(parts_list)
    ]
    layout.append([sg.Button('Select All'), sg.Button('Clear All'), sg.Button('SLICE'), sg.Button('Cancel')])

    window = sg.Window('Select Parts for Processing', layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancel'):
            print("User cancelled or closed the window.")
            break
        if event == 'Select All':
            for index in range(len(parts_list)):
                window[f'CHECK_{index}'].update(value=True)
        if event == 'Clear All':
            for index in range(len(parts_list)):
                window[f'CHECK_{index}'].update(value=False)
        if event == 'SLICE':
            new_parts_list = []
            for index, part in enumerate(parts_list):
                if values[f'CHECK_{index}']:
                    new_parts_list.append((part[0], int(values[f'QUANTITY_{index}'])))
            window.close()
            return new_parts_list


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
        else:
            raise ValueError(f'Invalid file or folder: {item_path}')
    return clean_file_dict(files)


def parts_data_from_file_dict(file_dict: dict) -> List[Tuple[str, int, str]]:
    """
    Extract parts data from a dictionary of files.

    Args:
        file_dict (dict): A dictionary of file paths, where the keys are the file names
        and the values are the full file paths.

    Returns:
        List[Tuple[str, int, str]]: A list of tuples representing parts, quantities, and file paths.
    """

    parts_data = []
    for key, value in file_dict.items():
        if isinstance(value, dict):
            parts_data.extend(parts_data_from_file_dict(value))
        else:
            parts_data.append([key, 1, value])
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

        mutated_parts_data = create_parts_ui(parts_data)
        
        # Slice each part
        for part_name, quantity, path_to_part in mutated_parts_data:
            print(f'Slicing {quantity} of {part_name}...')
            # Logic for slicing the part
            gcode_path = path_to_part.replace('.stl', '') + '.gcode'

        # Upload each part to a cloud service
        gcode_file_dict = create_dict_of_files(input_path, ['.gcode'])


if __name__ == "__main__":
    main()
