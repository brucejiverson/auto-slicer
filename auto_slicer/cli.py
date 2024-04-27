import click
import csv
from pathlib import Path
import requests

# Base configurations
CONFIG = {
    "api_endpoint": "http://octopi.local/api/",
    "api_key": "your_api_key_here"
}

def load_bom(bom_path: str):
    """Load the bill of materials (BOM) from a CSV file."""
    parts = []
    with open(bom_path, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            parts.append(row)
    return parts


def slice_model(stl_path: str, settings: dict):
    """Simulate the slicing process for an STL file."""
    print(f"Slicing {stl_path} with settings: {settings}")
    # Placeholder for actual slicing logic
    return f"{stl_path[:-4]}.gcode"  # Simulated G-code file path


def send_to_printer(gcode_path: str):
    """Send the G-code to the printer via OctoPi API."""
    print(f"Sending {gcode_path} to the printer")
    url = f"{CONFIG['api_endpoint']}files/local"
    headers = {
        "X-Api-Key": CONFIG["api_key"]
    }
    files = {'file': open(gcode_path, 'rb')}
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 201:
        print("Upload successful")
    else:
        print("Failed to upload file")


@click.group()
def cli():
    """Auto-Slicer CLI for managing 3D printing tasks."""
    pass


@cli.command()
@click.option('--directory', type=click.Path(exists=True), help='Directory containing STL files.')
@click.option('--bom', type=click.Path(exists=True), help='Path to the BOM file in CSV format.')
def process(directory, bom):
    """Process STL files as per the BOM and send them to the printer."""
    directory = Path(directory)
    parts = load_bom(bom)
    
    for part in parts:
        stl_path = directory / part['filename']
        if stl_path.exists():
            gcode_path = slice_model(stl_path, part['settings'])
            send_to_printer(gcode_path)
        else:
            print(f"File {stl_path} not found")

if __name__ == '__main__':
    cli()
