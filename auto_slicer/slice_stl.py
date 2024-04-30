import subprocess
import os

from auto_slicer.util import get_config_parameter



def slice_stl(file_path: str, output_folder_path: str = None, slicer_config_path: str = None) -> str:
    """Run PrusaSlicer with specific configuration settings to slice an STL file.

    Args:
        file_path (str): The path to the STL file.
        output_folder_path (str, optional): The path to the output folder for the sliced G-code.
        slicer_config_path (str, optional): The path to the slicer configuration file.

    Returns:
        str: The path to the sliced G-code file.
    """
    # Determine the slicer configuration file
    if slicer_config_path is None:
        slicer_config_path = get_config_parameter("slicer_config_path")
    # Set the output folder to the folder of the file_path if not specified
    if output_folder_path is None:
        output_folder_path = os.path.dirname(file_path)
    output_folder_path = os.path.abspath(output_folder_path)
    output_path = os.path.join(output_folder_path, os.path.splitext(os.path.basename(file_path))[0] + ".gcode")
    print(f'Output path: {output_path}')

    # Assemble the command
    slicer_command = [
        "prusa-slicer-console.exe",
        "--load", slicer_config_path,
        "--slice",
        "--export-gcode",
        "--output", output_path,  # Directly use the output path
        file_path  # Directly use the file path
    ]

    print(f'Command: {" ".join(slicer_command)}')

    try:
        # Run the command and capture output
        completed_process = subprocess.run(slicer_command, check=True, capture_output=True, text=True)
        print(completed_process.stdout)
    except subprocess.CalledProcessError as err:
        print("Error occurred while slicing:", err.stderr)
        raise RuntimeError(f"Slicing failed: {err.stderr}") from err

    print("\nSlicing complete.")
    return output_path


# def batch_slice(directory: Path, config: str):
#     """Batch process STL files for slicing in the specified directory."""
#     # Processing all '*.stl' files in the directory
#     stl_files = directory.glob("*.stl")
#     for file in stl_files:
#         slice_stl(file, config)


if __name__ == "__main__":

    stl_path = "auto_slicer/examples/AR4 servo gripper/AR4_SG1_base.STL"
    gcode_path = slice_stl(stl_path)
