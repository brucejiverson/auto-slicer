# tests/test_definitions.py
from auto_slicer.definitions import STLFile


def test_bom_line_item_basic():
    """Test basic STLFile creation and attributes"""
    item = STLFile("test_part", 1, "/path/to/file.stl")
    assert item.part_name == "test_part"
    assert item.quantity == 1
    assert item.file_path == "/path/to/file.stl"
    assert item.slice_warnings is None
    assert item.gcode_path is None


def test_bom_line_item_optional_fields():
    """Test STLFile with optional fields"""
    item = STLFile(
        "test_part",
        1,
        "/path/to/file.stl",
        slice_warnings="Test warning",
        gcode_path="/path/to/output.gcode"
    )
    assert item.slice_warnings == "Test warning"
    assert item.gcode_path == "/path/to/output.gcode"
