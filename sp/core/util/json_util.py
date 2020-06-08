import json


def load_content(json_data):
    """Load content of a json data.

    Args:
        json_data (object): json data. If a file name is passed, it loads the file
    Returns:
        Any: loaded data
    """
    if isinstance(json_data, str):
        with open(json_data) as json_file:
            return json.load(json_file)
    else:
        return json_data


def load_key_content(json_data, key):
    """Load content of a key in the json data as a dictionary.
    If the content indexed by the key is a file name, then it loads the file as a json file

    Args:
        json_data (dict): json data.
        key (object): a dictionary key
    Returns:
        Any: loaded data
    Raises:
        KeyError: key not found in the data
    """
    if key not in json_data:
        raise KeyError

    content = load_content(json_data[key])
    if isinstance(content, dict) and key in content:
        content = content[key]
    return content

