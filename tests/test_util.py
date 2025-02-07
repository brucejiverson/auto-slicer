# tests/test_util.py
from unittest.mock import patch
from auto_slicer.util import get_config_parameter, set_config_parameter


def test_get_config_parameter(mock_config_file):
    with patch('auto_slicer.util.config_path', str(mock_config_file)):
        value = get_config_parameter("url")
        assert value == "http://test.local"


def test_set_config_parameter(mock_config_file):
    with patch('auto_slicer.util.config_path', str(mock_config_file)):
        set_config_parameter("new_param", "new_value")
        value = get_config_parameter("new_param")
        assert value == "new_value"
