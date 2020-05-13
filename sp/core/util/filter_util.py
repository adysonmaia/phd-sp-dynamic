from future.utils import iteritems


def filter_dict_by_key(data, keys):
    """Filter a dictionary by a list of keys.
    Resulted dictionary that only contains the specified keys

    Args:
        data (dict): dictionary to be filtered
        keys (list): list of keys. If None, the original dict is returned
    Returns:
        dict: filtered dictionary
    """

    filtered_dict = None
    if keys is None:
        filtered_dict = data
    else:
        if not isinstance(keys, list):
            keys = [keys]
        filtered_dict = {}
        for key in keys:
            try:
                filtered_dict[key] = data[key]
            except KeyError:
                pass

    return filtered_dict


def filter_dict_by_value(data, values, attribute=None):
    """Filter a dictionary by a list of values.
    Resulted dictionary that only contains the specified values

    Args:
        data (dict): dictionary to be filtered
        values (list): list of values. If None, the original dict is returned
        attribute (str): check the attribute value for each item in the dict. If None, the item is used as the value
    Returns:
         dict: filtered dictionary
    """

    filtered_dict = None
    if values is None:
        filtered_dict = data
    else:
        if not isinstance(values, list):
            keys = [values]

        filtered_dict = {}
        for (key, item) in iteritems(data):
            value = None
            if attribute is not None:
                value = getattr(item, attribute, None)
            else:
                value = item

            if value in values:
                filtered_dict[key] = item

    return filtered_dict
