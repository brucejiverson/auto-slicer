import subprocess
from pathlib import Path


def slice_stl(file_path: Path, config: str):
    """Run PrusaSlicer with specific configuration settings."""
    slicer_command = [
        "/Applications/Original Prusa Drivers/PrusaSlicer.app/Contents/MacOS/PrusaSlicer",
        "--load", config,
        "--printer-technology", "FFF",
        "--center", "125,105",  # Assuming you want all parts centered
        "--slice",
        "--export-gcode",
        "--output", str(file_path.with_suffix('.gcode'))  # Specify output filename
    ]

    slicer_command.append(str(file_path))  # Add the STL file to the command

    print(f"Slicing {file_path}...")
    subprocess.run(slicer_command, check=True)


def batch_slice(directory: Path, config: str):
    """Batch process STL files for slicing in the specified directory."""
    # Processing all '*.stl' files in the directory
    stl_files = directory.glob("*.stl")
    for file in stl_files:
        slice_stl(file, config)


# Example usage
config_ini_path = "/path/to/config.ini"  # Adjust the path to your config.ini
stl_directory = Path("/path/to/stl/files")  # Adjust the directory path to your STL files
batch_slice(stl_directory, config_ini_path)
