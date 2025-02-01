from dataclasses import dataclass


@dataclass
class BoMLineItem:
    """
    Represents a Bill of Materials (BoM) line item.

    Attributes:
        part_name (str): The name of the part.
        quantity (int): The quantity of the part.
        file_path (str): The file path associated with the part.
        slice_warnings (str): Any warnings generated during the slicing process.
        gcode_path (str): The G-code file path associated with the part.
    """
    part_name: str
    quantity: int
    file_path: str
    slice_warnings: str = None
    gcode_path: str = None
