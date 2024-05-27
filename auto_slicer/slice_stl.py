import subprocess
import os
import logging

from auto_slicer.util import get_config_parameter


logger = logging.getLogger(__name__)
print(__name__)


def slice_stl_brute_force_rotation_no_support(stl_path: str, output_folder_path: str | None = None) -> str:
    """Slices an STL file and attempts rotations on two axes in 90-degree increments if needed due to warnings.

    Args:
        stl_path (str): Path to the STL file.
        output_folder_path (str | None): Folder to save the sliced G-code files (optional, defaults to same folder as STL file).

    Returns:
        str: Path to the successfully sliced G-code file, or None if failed after all rotations.
    """
    max_rotation = 360
    slicer_config_path = get_config_parameter("slicer_config_path")

    if output_folder_path is None:
        output_folder_path = os.path.dirname(stl_path)
    output_folder_path = os.path.abspath(output_folder_path)

    # Try rotations on Y-axis
    for rotation in range(0, max_rotation, 90):
        if slice_stl_no_support(stl_path, slicer_config_path, output_folder_path, rotation, 'y'):
            return slice_stl_no_support(stl_path, slicer_config_path, output_folder_path, rotation, 'y')

    # Try rotations on X-axis
    for rotation in range(0, max_rotation, 90):
        if slice_stl_no_support(stl_path, slicer_config_path, output_folder_path, rotation, 'x'):
            return slice_stl_no_support(stl_path, slicer_config_path, output_folder_path, rotation, 'x')

    raise RuntimeError("Failed to slice without warnings after all rotations.")


def slice_stl_no_support(stl_path, config_path, output_folder, degrees, axis):
    output_file_name = f"{os.path.splitext(os.path.basename(stl_path))[0]}.gcode"
    output_path = os.path.join(output_folder, output_file_name)
    slicer_command = [
        "prusa-slicer-console.exe",
        "--load", config_path,
        f"--rotate-{axis}", str(degrees),
        "--slice",
        "--export-gcode",
        "--output", output_path,
        stl_path
    ]

    logger.debug(f"Slicing with {axis.upper()} rotation {degrees} degrees...")
    try:
        result = subprocess.run(slicer_command, check=True, capture_output=True, text=True)
        logger.debug(result.stdout)
        if "Detected print stability issues" not in result.stdout:
            logger.info("Slicing successful with no warnings.")
            return output_path
    except subprocess.CalledProcessError as err:
        logger.error("Error during slicing:", err.stderr)

    return None


if __name__ == "__main__":

    stl_path = "auto_slicer/examples/AR4 servo gripper/AR4_SG1_base.STL"
    gcode_path = slice_stl_brute_force_rotation_no_support(stl_path)
