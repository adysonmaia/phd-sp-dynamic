class Resource:
    """Resource Model Class
    it it used to store properties of a type of resource that can allocated in a Node

    Attributes:
        name (str): Unique identification of the resource. E.g., 'CPU', 'RAM', 'STORE'
        unit (str): Measured unit of the resource. E.g., 'IPS', 'MB', 'GB'
        type (str): Type of variable used to store an amount of the resource. E.g., 'float', 'int'
        precision (int): precision of variable that stores a specific amount of the resource
    """
    CPU = "CPU"

    def __init__(self):
        """Initialization
        """
        self.name = ""
        self.unit = ""
        self.type = "float"
        self.precision = 4

    @property
    def id(self):
        """Unique identification of the resource, which it is its name
        Returns:
             str: resource's id
        """
        return self.name

    def __eq__(self, other):
        """Check if a resource is equal to other
        Two resource are equals if they have the same identification

        Args:
             other (Resource): other resource
        Returns:
            bool: two resource are equals
        """
        return self.id == other.id

    @staticmethod
    def from_json(json_data):
        """Create a Resource object from a json data
        See :py:func:`sp.core.model.resource.from_json`
        Args:
           json_data (dict): data loaded from a json
        Returns:
           Resource: loaded resource
        """
        return from_json(json_data)


def from_json(json_data):
    """Create a Resource object from a json data
    Only the 'name' key is required from the json dict data

    .. code-block:: python
        # Only the required properties
        json_data = {'name': 'CPU'}
        resource = sp.core.model.resource.from_json(json_data)

        # With optional properties
        json_data = {'name': 'CPU', 'unit': 'IPS'  'type': 'float', 'precision': 5}
        resource = sp.core.model.resource.from_json(json_data)

    Args:
        json_data (dict): data loaded from a json
    Returns:
        Resource: loaded resource
    Raises:
        KeyError: Attribute not found
    """
    r = Resource()
    if isinstance(json_data, str):
        r.name = str(json_data).upper()
    elif isinstance(json_data, dict):
        r.name = str(json_data["name"]).upper()
        if "unit" in json_data:
            r.unit = str(json_data["unit"])
        if "type" in json_data:
            r.type = str(json_data["type"]).lower()
        if "precision" in json_data:
            r.precision = int(json_data["precision"])
    else:
        raise TypeError

    return r


