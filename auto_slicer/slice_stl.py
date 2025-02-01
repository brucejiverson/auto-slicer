import re
import subprocess
import os
import logging

from auto_slicer.util import get_config_parameter


logger = logging.getLogger(__name__)


def estimate_nozzle_and_layer_height(gcode_file: str) -> tuple[float, float]:
    """
    Estimate the nozzle diameter and layer height from the G-code file.

    Args:
        gcode_file (str): Path to the G-code file.

    Returns:
        tuple[float, float]: A tuple containing the estimated nozzle diameter (mm) and layer height (mm).
    """
    nozzle_diameter = None
    layer_height = None

    nozzle_re = re.compile(
        r';\s*nozzle_diameter\s*=\s*([\d.]+)',
        re.IGNORECASE)
    layer_height_re = re.compile(
        r';\s*layer_height\s*=\s*([\d.]+)',
        re.IGNORECASE)

    with open(gcode_file, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()

            # Look for nozzle diameter
            nozzle_match = nozzle_re.search(line)
            if nozzle_match:
                nozzle_diameter = float(nozzle_match.group(1))

            # Look for layer height
            layer_height_match = layer_height_re.search(line)
            if layer_height_match:
                layer_height = float(layer_height_match.group(1))

            # Stop searching once both values are found
            if nozzle_diameter is not None and layer_height is not None:
                break

    if nozzle_diameter is None or layer_height is None:
        raise ValueError(
            "Could not estimate nozzle diameter or layer height from the G-code file.")

    return nozzle_diameter, layer_height


def estimate_support_volume(
        gcode_file: str,
        nozzle_diameter: float,
        layer_height: float) -> float:
    """
    Calculate the volume of support material from a G-code file.

    Args:
        gcode_file (str): Path to the G-code file.
        nozzle_diameter (float): Diameter of the 3D printer nozzle (in mm).
        layer_height (float): Layer height of the 3D print (in mm).

    Returns:
        float: Volume of support material (in cubic millimeters).
    """
    support_volume = 0.0
    is_support = False
    extrusion_re = re.compile(r'G1 .*?E([\d.]+)')

    with open(gcode_file, 'r', encoding='utf-8') as file:
        last_extrusion = 0.0

        for line in file:
            line = line.strip()

            # Detect support material using the updated comment
            if ";TYPE:Support material" in line:
                is_support = True
            # Detect the start of a new type (e.g., perimeters, infill)
            elif ";TYPE:" in line:
                is_support = False

            # Check for extrusion commands
            match = extrusion_re.search(line)
            if match and is_support:
                current_extrusion = float(match.group(1))
                extruded_length = current_extrusion - last_extrusion
                last_extrusion = current_extrusion

                # Calculate volume: π * (radius^2) * extruded_length
                radius = nozzle_diameter / 2
                support_volume += 3.14159 * (radius ** 2) * extruded_length

    return support_volume


def estiamte_non_support_volume(
        gcode_file: str,
        nozzle_diameter: float,
        layer_height: float) -> float:
    """
    Calculate the volume of non-support material from a G-code file.

    Args:
        gcode_file (str): Path to the G-code file.
        nozzle_diameter (float): Diameter of the 3D printer nozzle (in mm).
        layer_height (float): Layer height of the 3D print (in mm).

    Returns:
        float: Volume of non-support material (in cubic millimeters).
    """
    non_support_volume = 0.0
    is_support = False
    extrusion_re = re.compile(r'G1 .*?E([\d.]+)')

    with open(gcode_file, 'r', encoding='utf-8') as file:
        last_extrusion = 0.0

        for line in file:
            line = line.strip()

            # Detect support material using the updated comment
            if ";TYPE:Support material" in line:
                is_support = True
            # Detect the start of a new type (e.g., perimeters, infill)
            elif ";TYPE:" in line:
                is_support = False

            # Check for extrusion commands
            match = extrusion_re.search(line)
            if match and not is_support:
                current_extrusion = float(match.group(1))
                extruded_length = current_extrusion - last_extrusion
                last_extrusion = current_extrusion

                # Calculate volume: π * (radius^2) * extruded_length
                radius = nozzle_diameter / 2
                non_support_volume += 3.14159 * (radius ** 2) * extruded_length

    return non_support_volume


def estimate_fraction_of_support_material(gcode_file: str) -> float:
    """
    Estimate the fraction of support material in a G-code file.

    Args:
        gcode_file (str): Path to the G-code file.

    Returns:
        float: Fraction of support material.
    """
    nozzle_diameter_mm, layer_height_mm = estimate_nozzle_and_layer_height(
        gcode_file)
    support_volume = estimate_support_volume(
        gcode_file, nozzle_diameter_mm, layer_height_mm)
    non_support_volume = estiamte_non_support_volume(
        gcode_file, nozzle_diameter_mm, layer_height_mm)

    total_volume = support_volume + non_support_volume

    if total_volume == 0:
        raise ValueError("Total volume is zero, cannot calculate fraction.")

    # Display results
    print(f"Nozzle diameter: {nozzle_diameter_mm} mm")
    print(f"Layer height: {layer_height_mm} mm")
    print(f"Support material volume: {support_volume:.2f} mm³")
    print(f"Non-support material volume: {non_support_volume:.2f} mm³")
    print(f'Fraction of support material: {support_volume / total_volume:.2f}')
    return support_volume / total_volume


def slice_stl_brute_force_rotation_no_support(
        stl_path: str,
        slicer_config_path: str,
        output_folder_path: str | None = None) -> str:
    """Slices an STL file and attempts rotations on two axes in 90-degree increments if needed due to warnings.

    Args:
    stl_path (str): Path to the STL file.
    slicer_config_path (str): Path to the slicer configuration file.
    output_folder_path (str | None): Folder to save the sliced G-code files
    (optional, defaults to same folder as STL file).

    Returns:
    str: Path to the successfully sliced G-code file.
    """
    max_rotation = 360

    if output_folder_path is None:
        output_folder_path = os.path.dirname(stl_path)
    output_folder_path = os.path.abspath(output_folder_path)

    generated_files = []

    # Try rotations on Y-axis
    for rotation in range(0, max_rotation, 90):
        sliced_path = slice_stl_no_support(
            stl_path, slicer_config_path, output_folder_path, rotation, 'y')
        if sliced_path is not None:
            # delete previously generated files and return the current one
            for file in generated_files:
                os.remove(file)

            return sliced_path
        if sliced_path is not None:
            generated_files.append(sliced_path)

    # Try rotations on X-axis
    for rotation in (90, 270):
        sliced_path = slice_stl_no_support(
            stl_path, slicer_config_path, output_folder_path, rotation, 'x')
        if sliced_path is not None:
            # delete previously generated files and return the current one
            for file in generated_files:
                os.remove(file)
            return sliced_path
        if sliced_path is not None:
            generated_files.append(sliced_path)

    raise RuntimeError("Failed to slice without warnings after all rotations.")


def slice_stl_no_support(
        stl_path: str,
        config_path: str,
        output_folder: str,
        degrees: int,
        axis: str) -> str | None:
    """Slices an STL file without support and rotates it by a specified degree on a specified axis.

    Useful references:
        - https://github.com/prusa3d/PrusaSlicer/wiki/Command-Line-Interface
        - https://manual.slic3r.org/advanced/command-line

    Args:
        stl_path (str): Path to the STL file.
        config_path (str): Path to the slicer configuration file.
        output_folder (str): Folder to save the sliced G-code file.
        degrees (int): Degrees to rotate the STL file.
        axis (str): Axis to rotate the STL file ('x' or 'y').

    Returns:
        str | None: Path to the successfully sliced G-code file, or None if slicing failed.
    """
    output_file_name = f"{
        os.path.splitext(
            os.path.basename(stl_path))[0]}.gcode"
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

    logger.debug(
        "Slicing with %s rotation %d degrees...",
        axis.upper(),
        degrees)

    try:
        result = subprocess.run(
            slicer_command,
            check=True,
            capture_output=True,
            text=True)
        logger.debug(result.stdout)
        if "Detected print stability issues" not in result.stdout:
            logger.info("Slicing successful with no warnings.")
            return output_path
        else:
            # get the location of the error message
            warning_start_idx = result.stdout.index(
                "Detected print stability issues:")
            warning_start_idx += len("Detected print stability issues:") + 1

            # find the next newline character after the warning start
            warning_end_idx = result.stdout.index("\n", warning_start_idx)
            logger.debug(
                'warning idxs %d %d',
                warning_start_idx,
                warning_end_idx)
            logger.debug('Detected warnings: %s',
                         result.stdout[warning_start_idx:warning_end_idx])

            estimate_fraction_of_support_material(output_path)

    except subprocess.CalledProcessError as err:
        logger.error("Error during slicing: %s", err.stderr)
    return None
