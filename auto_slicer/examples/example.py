

import os
import sys
import FreeCAD as App
import Part
import Mesh

def process_step_assembly(input_file: str, output_folder: str) -> None:
    """
    Process a STEP assembly file, record metadata for each part, and export to STL.

    Args:
    input_file (str): Path to the input STEP file.
    output_folder (str): Directory to save the converted STL files and metadata.
    """
    # Set up paths
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    stl_folder = os.path.join(output_folder, "Converted-STLs")
    if not os.path.exists(stl_folder):
        os.makedirs(stl_folder)
    
    # Load the STEP file
    doc = App.openDocument(input_file)
    doc.recompute()

    # Metadata storage
    metadata = []

    # Process each object in the document
    for obj in doc.Objects:
        if hasattr(obj, "Shape") and obj.Shape.isValid():
            # Export to STL
            stl_path = os.path.join(stl_folder, f"{obj.Name}.stl")
            Mesh.export([obj], stl_path)

            # Calculate metadata (placeholders for example)
            volume = obj.Shape.Volume  # in cubic mm
            material_volume = volume  # assuming solid fill, in cubic mm
            bed_area = obj.Shape.BoundBox.XLength * obj.Shape.BoundBox.YLength  # in square mm
            height = obj.Shape.BoundBox.ZLength  # in mm

            # Append metadata
            metadata.append({
                "Name": obj.Name,
                "STL Path": stl_path,
                "Volume (mm^3)": volume,
                "Material Volume (mm^3)": material_volume,
                "Bed Area (mm^2)": bed_area,
                "Height (mm)": height,
                "Estimated Print Time (hours)": 0,  # Placeholder
                "Material Cost": 0  # Placeholder
            })

    # Optionally, save or print metadata
    print(metadata)

    # Clean up
    doc.close()

# Example usage
process_step_assembly("path_to_step_file.step", "output_directory")





if __name__ == '__main__':
    import sys
    sys.path.append('..')
    
    import os
    from pathlib import Path
    
    # this directory
    assembly_step_path = Path(os.getcwd()) / 'Assembly Test 02.step' 