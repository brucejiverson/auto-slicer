# tests/test_ui.py
from auto_slicer.ui import create_dict_of_files, parts_data_from_file_dict
from auto_slicer.definitions import STLFile


def test_create_dict_of_files(test_data_dir):
    # Create test files
    (test_data_dir / "test1.stl").touch()
    (test_data_dir / "test2.step").touch()
    (test_data_dir / "subdir").mkdir()
    (test_data_dir / "subdir" / "test3.stl").touch()

    result = create_dict_of_files(str(test_data_dir), ['.stl', '.step'])
    assert len(result) > 0
    assert any('.stl' in str(path) for path in result[test_data_dir.name])


def test_parts_data_from_file_dict():
    file_dict = {
        "folder1": ["/path/to/part1.stl", "/path/to/part2.stl"],
        "folder2": {"subfolder": ["/path/to/part3.stl"]}
    }

    result = parts_data_from_file_dict(file_dict)
    assert len(result) == 3
    assert all(isinstance(item, STLFile) for item in result)
