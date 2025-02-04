from typing import List, Optional
from enum import StrEnum
from dataclasses import dataclass


@dataclass
class STLFile:
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
    slice_warnings: Optional[str] = None
    gcode_path: Optional[str] = None

    def __repr__(self):
        representation = ""
        for field in self.__dataclass_fields__:
            value = getattr(self, field)
            if value is not None:
                representation += f", {field.upper()} {value}"
        return representation


@dataclass
class STLBoM:
    """
    Represents a Bill of Materials (BoM) for a project.

    Attributes:
        project_name (str): The name of the project.
        parts (List[STLFile]): The parts associated with the project.
    """
    project_name: str
    parts: List[STLFile]

    def __repr__(self):
        representation = f"Project Name: {self.project_name}\n"
        for part in self.parts:
            representation += f"{part}\n"
        return representation


class RemoteObjectTypes(StrEnum):
    """An enumeration of the types of files that can be stored on a remote target."""
    FOLDER = 'folder'
    FILE = 'file'


@dataclass
class RemoteFile:
    """A standard format to represent files or folders on a remote target. 

    Nominally based on the metadata associated with Octopi files.

    Folder example: {'children': [], 'date': 1738558602, 'display': 'gridfinity ', 'name': 'gridfinity', 'origin': 'local', 'path': 'gridfinity', 'prints': {'failure': 0, 'success': 0}, 'refs': {'resource': 'http://octopi.local/api/files/local/gridfinity'}, 'size': 67149615, 'type': 'folder', 'typePath': ['folder']}
    File example: 


    Attributes:
        name (dict): The name of the file.
        date (int): The date the file was created.
        display (str): The display name of the file.
        gcodeAnalysis (dict): The analysis of the G-code file.
        hash (str): The hash of the file.
        name (str): The name of the file.
        origin (str): The origin of the file.
        path (str): The path of the file.
        prints (dict): The print history of the file.
        refs (dict): References to the file.
        size (int): The size of the file.
        statistics (dict): The statistics of the file.
        type (RemoteObjectTypes): The type of the file.
        children (Optional[List[RemoteFile]]): The children of the file.
    """
    name: dict
    date: int
    display: str            # display name
    gcodeAnalysis: dict
    hash: str
    name: str
    origin: str
    path: str
    prints: dict
    refs: dict
    size: int
    statistics: dict
    type: RemoteObjectTypes
    children: Optional[List["RemoteFile"]] = None
