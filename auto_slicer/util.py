import json


def get_config_parameter(parameter: str) -> str:
    """Reads from config.json and returns the matching value

    Returns:
        str: The key 
    """
    with open('config.json', 'r') as f:
        data = json.load(f)
        return data[parameter]
