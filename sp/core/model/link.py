class Link:
    """Link Model Class

    It is used to store properties of a network link.
    A link connects two node and its represents an undirected edge in the graph

    Attributes:
        nodes_id (tuple): Ids of connected nodes
        bandwidth (float): The link's bandwidth
        propagation_delay (float): The propagation delay of the link
    """
    def __init__(self):
        """Initialization
        """
        self.nodes_id = (-1, -1)
        self.bandwidth = 0.0
        self.propagation_delay = 0.0

    def __eq__(self, other):
        """Check if a link is equal to other.
        The comparison takes into consideration that links are undirected edges in a graph

        Args:
            other (Link): other link
        Returns:
            bool: if the link is equal to other
        """
        if other is None:
            return False
        ids_1 = self.nodes_id
        ids_2 = other.nodes_id
        ids_3 = ids_2[::-1]
        return (ids_1 == ids_2) or (ids_1 == ids_3)

    @staticmethod
    def from_json(json_data):
        """Create a link object from a json data

        See :py:func:`sp.core.model.link.from_json`

        Args:
           json_data (dict): data loaded from a json
        Returns:
           Link: loaded link
        """
        return from_json(json_data)


def _nodes_from_json(json_data):
    """Load nodes id of a link from json

    E.g.:

    .. code-block:: python

        # Ids passed as list
        json_data = {'nodes': [0, 1]}
        nodes_id = _nodes_from_json(json_data['nodes'])

        # Ids passed as tuple
        json_data = {'nodes': (0, 1)}
        nodes_id = _nodes_from_json(json_data['nodes'])

        # Ids passed as dict
        json_data = {'nodes': {'s': 0, 'd': 0}}
        nodes_id = _nodes_from_json(json_data['nodes'])

    Args:
        json_data (Union[list, tuple, dict]): data loaded from a json
    Returns:
        tuple: nodes' id
    Raises:
        KeyError: Attribute not found
    """
    if isinstance(json_data, list) or isinstance(json_data, tuple):
        return int(json_data[0]), int(json_data[1])
    elif isinstance(json_data, dict):
        return int(json_data["s"]), int(json_data["d"])
    else:
        raise TypeError


def from_json(json_data):
    """Create a Link object from a json data

    E.g.:

    .. code-block:: python

        json_data = {
            'nodes': [0, 1],  # Nodes' id
            'bw': 2e+10,  # Bandwidth
            'delay': 10.0  # Propagation delay
        }
        node = sp.core.model.link.from_json(json_data)

    Args:
        json_data (dict): data loaded from a json
    Returns:
        Link: loaded link
    Raises:
        KeyError: Attribute not found
    """
    link = Link()
    link.nodes_id = _nodes_from_json(json_data["nodes"])
    link.bandwidth = float(json_data["bw"])
    link.propagation_delay = float(json_data["delay"])
    return link
