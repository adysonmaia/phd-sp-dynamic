import json


def load_content(json_data):
    if isinstance(json_data, str):
        with open(json_data) as json_file:
            return json.load(json_file)
    else:
        return json_data


def load_key_content(json_data, key):
    if key not in json_data:
        raise TypeError

    content = load_content(json_data[key])
    if isinstance(content, dict) and key in content:
        content = content[key]
    return content

