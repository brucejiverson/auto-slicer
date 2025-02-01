import os
import logging
import asyncio

from auto_slicer import octopi_integration
from auto_slicer import slice_stl
from auto_slicer import ui
from auto_slicer.definitions import BoMLineItem

logger = logging.getLogger(__name__)


async def main():
    """
    Main function to handle the slicing and uploading of 3D model files.
    This function performs the following steps:
    1. Prompts the user to select a file or folder using a UI.
    2. If a file is selected, creates a list with a single BoMLineItem.
    3. If a folder is selected, creates a dictionary of files with specific extensions and generates parts data.
    4. Displays the parts data to the user for potential modification.
    5. Slices each part using a brute force rotation method without support.
    6. Uploads the generated G-code files to a cloud service.
    The function logs various debug and info messages throughout the process.
    Returns:
        None
    """

    input_path = await ui.create_stl_file_selection_ui()
    if input_path:
        if os.path.isfile(input_path):
            parts_data = [
                BoMLineItem(
                    os.path.basename(input_path),
                    1,
                    input_path)]

        else:
            # Logic for processing a folder
            file_dict = ui.create_dict_of_files(
                input_path, ['.step', '.stp', '.stl'])
            logger.debug("File dict: %s", file_dict)
            parts_data = ui.parts_data_from_file_dict(file_dict)

        logger.debug("Parts data: %s", parts_data)
        mutated_parts_data = ui.create_part_selection_ui(parts_data)
        logger.debug("Mutated parts data: %s", mutated_parts_data)

        # select slicer configuration file
        slicer_config_files = [f for f in os.listdir(
            './slicer_profiles') if f.endswith('.ini')]
        logger.debug("Slicer config files: %s", slicer_config_files)

        if len(slicer_config_files) == 0:
            raise FileNotFoundError(
                "No slicer configuration files found in the slicer_profiles folder.")
        elif len(slicer_config_files) == 1:
            slicer_config_path = os.path.join(
                './slicer_profiles', slicer_config_files[0])
            logger.info(
                "Using slicer configuration file: %s",
                slicer_config_path)
        else:
            logger.info("Multiple slicer configuration files found.")
            slicer_config_file = ui.create_slicer_config_selection_ui(
                slicer_config_files)
            slicer_config_path = os.path.join(
                './slicer_profiles', slicer_config_file)
            logger.info(
                "Using slicer configuration file: %s",
                slicer_config_path)

        # Slice each part
        outputs = []
        for bom_item in mutated_parts_data:
            logger.info('Slicing %s.', bom_item.part_name)
            # Logic for slicing the part
            output = slice_stl.slice_stl_brute_force_rotation_no_support(
                bom_item.file_path,
                slicer_config_path
            )
            bom_item.gcode_path = output
            outputs.append(output)

        logger.info("Outputs: %s", outputs)
        # Upload each part to a cloud service
        gcode_file_dict = ui.create_dict_of_files(input_path, ['.gcode'])
        logger.debug("Gcode file dict: %s", gcode_file_dict)
        # gcode_file_dict is a heirarchical dictionary of files with the values
        # being the file paths. clean out against the outputs list

        def find_keys_to_remove(d, outputs):
            keys_to_remove = []
            for key, value in d.items():
                if isinstance(value, dict):
                    keys_to_remove.extend(find_keys_to_remove(value, outputs))
                elif value not in outputs:
                    keys_to_remove.append(key)
                return keys_to_remove

        keys_to_remove = find_keys_to_remove(gcode_file_dict, outputs)
        for key in keys_to_remove:
            logger.debug(
                "G-code file %s not found in outputs list.",
                gcode_file_dict[key])
            del gcode_file_dict[key]
        logger.debug("G-code file dict after cleaning: %s", gcode_file_dict)
        octopi_integration.upload_nested_dict_to_octopi(gcode_file_dict)


def poetry_main():
    """
    Entry point for the auto_slicer application when using Poetry.
    This function initializes the asyncio event loop and runs the main coroutine
    until it completes.
    Note:
        Ensure that the `main` coroutine is defined elsewhere in the codebase.
    Raises:
        Any exceptions raised by the `main` coroutine.
    """

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            pass
    loop.close()
