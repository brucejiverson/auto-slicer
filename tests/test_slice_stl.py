
# tests/test_slice_stl.py
import pytest
from unittest.mock import patch, MagicMock
from auto_slicer.slice_stl import (
    slice_stl_no_support,
    estimate_fraction_of_support_material,
    estimate_nozzle_and_layer_height
)


@pytest.fixture
def mock_subprocess():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            stdout="Success\n",
            returncode=0
        )
        yield mock_run


def test_slice_stl_no_support_success(
        mock_subprocess,
        sample_stl_file,
        mock_slicer_config):
    result = slice_stl_no_support(
        str(sample_stl_file),
        str(mock_slicer_config),
        str(sample_stl_file.parent),
        0,
        'y'
    )
    assert result is not None
    mock_subprocess.assert_called_once()


def test_estimate_nozzle_and_layer_height(test_data_dir):
    gcode_content = """
; Generated by PrusaSlicer
; nozzle_diameter = 0.4
; layer_height = 0.2
"""
    gcode_file = test_data_dir / "test.gcode"
    with open(gcode_file, "w", encoding="utf-8") as f:
        f.write(gcode_content)

    nozzle, layer = estimate_nozzle_and_layer_height(str(gcode_file))
    assert nozzle == 0.4
    assert layer == 0.2
