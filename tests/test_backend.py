import os
import logging
import asyncio

from auto_slicer import octopi_integration as op
from auto_slicer import slice_stl
from auto_slicer import ui
from auto_slicer.definitions import STLFile, STLBoM
from auto_slicer import util

logger = logging.getLogger(__name__)


async def test_slice_and_upload_backend():
    """
    Main function to handle the slicing and uploading of 3D model files.
    This function performs the following steps:
    1. Prompts the user to select a file or folder using a UI.
    2. If a file is selected, creates a list with a single STLFile.
    3. If a folder is selected, creates a dictionary of files with specific extensions and generates parts data.
    4. Displays the parts data to the user for potential modification.
    5. Slices each part using a brute force rotation method without support.
    6. Uploads the generated G-code files to a cloud service.
    The function logs various debug and info messages throughout the process.
    Returns:
        None
    """
    print(f'Current working directory: {os.getcwd()}')

    input_path = r".\tests\assets\chess_sign"
    assert os.path.exists(input_path), f"Path {input_path} does not exist."
    if os.path.isfile(input_path):
        parts_data = [
            STLFile(
                os.path.basename(input_path),
                1,
                input_path)]
    else:
        file_dict = util.create_dict_of_files(
            input_path, ['.step', '.stp', '.stl'])
        logger.debug("File dict: %s", file_dict)
        parts_data = util.parts_data_from_file_dict(file_dict)

    logger.debug("Parts data: %s", parts_data)
    bill_of_materials: STLBoM = STLBoM(
        project_name="Test project, chess sign",
        parts=parts_data
    )
    print(bill_of_materials)

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
    for bom_item in bill_of_materials.parts:
        logger.info('Slicing %s.', bom_item.part_name)
        # Logic for slicing the part
        output = slice_stl.slice_stl_brute_force_rotation_no_support(
            bom_item.file_path,
            slicer_config_path
        )
        bom_item.gcode_path = output

    await op.upload_files_to_octopi(bill_of_materials)
    await op.create_and_configure_continuous_print_job(bill_of_materials)

    # import time
    # parts = (
    #     'Test project, chess_sign/rim.gcode',
    #     'Test project, chess_sign/Black to move.gcode',
    #     'Test project, chess_sign/White to move.gcode'
    # )
    # time.sleep(1)
    # response = op.add_set_to_continous_print(
    #     path='Test project, chess_sign/rim',
    #     job_name="chess_sign",
    #     job_draft=True)
    # job_id = response['job_id']
    # time.sleep(1)
    # op.add_set_to_continous_print(
    #     path='Test project, chess_sign/Black to move',
    #     job_name="chess_sign",
    #     job_id=job_id,
    #     job_draft=True)
    # time.sleep(1)
    # op.add_set_to_continous_print(
    #     path='Test project, chess_sign/White to move',
    #     job_name="chess_sign",
    #     job_id=job_id,
    #     job_draft=False)


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_slice_and_upload_backend())
    loop.close()
