
# tests/conftest.py
import pytest
import json
import tempfile
from pathlib import Path


@pytest.fixture
def test_data_dir():
    """Creates a temporary directory for test data"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_config_file(test_data_dir):
    """Creates a temporary config file for testing"""
    config_data = {
        "url": "http://test.local",
        "octoprint_api_key": "test_key"
    }
    config_file = test_data_dir / "config.json"

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f)

    return config_file


@pytest.fixture
def sample_stl_content():
    """Returns minimal valid STL file content"""
    return """
solid cube
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 1 0 0
      vertex 1 1 0
    endloop
  endfacet
endsolid cube
"""


@pytest.fixture
def sample_stl_file(test_data_dir, sample_stl_content):
    """Creates a temporary STL file for testing"""
    stl_file = test_data_dir / "test.stl"

    with open(stl_file, "w", encoding="utf-8") as f:
        f.write(sample_stl_content)

    return stl_file


@pytest.fixture
def mock_slicer_config(test_data_dir):
    """Creates a mock slicer configuration file"""
    config_content = """
[print:default]
layer_height = 0.2
support_material = 0
infill_density = 20%
"""
    config_file = test_data_dir / "test_config.ini"

    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config_content)

    return config_file
