from sp.core.model import Resource
from sp.core.geometry import point
from sp.core.estimator import polynomial
from sp.core.estimator import power
from future.utils import iteritems
from functools import total_ordering


@total_ordering
class Node:
    """Node Model Class
    it it used to store properties of a node. A node can act as a network, access point, and/or computer node

    Attributes:
        id (int): Unique identification of the node
        type (str): Type of the node. E.g., a node can be a baste station (BS), a cloud data center (CLOUD)
            or be in the core of a mobile network (CORE)
        availability (float): It is the probability that the node will not fail, 0 <= value <= 1
        capacity (dict): For each resource, it specifies the total capacity for this resource on the node.
            The dictionary's keys are the resource names and the values are floats
        cost (dict): For each resource, it presents a function to calculate the cost for allocating a specified
            amount of resources. The dictionary's keys are the resource names and the values are
            estimator :py:class:`sp.core.estimator.Estimator` objects.
            Use :py:meth:`sp.core.estimator.Estimator.calc` or :py:meth:`sp.core.estimator.Estimator.__call__`
            to obtain the cost. E.g.:

            .. code-block:: python

                # Using the __call__ method
                resource_name = 'CPU'
                amount = 5.0
                app.cost[resource_name](amount)

                # Or using the calc method
                app.demand[resource_name].calc(amount)

        power_consumption (sp.core.estimator.power.PowerEstimator): it is a estimator of the power consumption of the
            node based on the CPU utilization.
        position (sp.core.geometry.point.Point): node's position

    """
    BS_TYPE = "BS"
    CORE_TYPE = "CORE"
    CLOUD_TYPE = "CLOUD"

    def __init__(self):
        """Initialization
        """
        self.id = -1
        self.type = ""
        self.availability = 0.0
        self.capacity = {}
        self.cost = {}
        self.power_consumption = None
        self.position = None

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    @property
    def cpu_capacity(self):
        """Get the CPU capacity of the node
        Returns:
             float: capacity value
        """
        return self.capacity[Resource.CPU]

    def is_base_station(self):
        """Check if the node is a base station
        Returns:
            bool: True if the node is a base station
        """
        return self.type == self.BS_TYPE

    def is_core(self):
        """Check if the node's type is CORE
        Returns:
            bool: True if the node is a core node
        """
        return self.type == self.CORE_TYPE

    def is_cloud(self):
        """Check if the node is a cloud data center
        Returns:
            bool: True if the node is a cloud data center
        """
        return self.type == self.CLOUD_TYPE

    @staticmethod
    def from_json(json_data):
        """Create a node object from a json data
        See :py:func:`sp.core.model.node.from_json`
        Args:
            json_data (dict): data loaded from a json
        Returns:
            Node: loaded node
        """
        return from_json(json_data)


def from_json(json_data):
    """Create a Node object from a json data.

    It loads the power consumption as a linear function using :py:class:`sp.core.estimator.power.LinearPowerEstimator`

    The node's position can be either on point in a cartesian plan
    :py:class:`sp.core.geometry.point.cartesian.CartesianPoint`

    .. code-block:: python

        x, y, z = 0.0, 1.0, 2.0
        json_data = {'position': [x, y]} #  2D Plan
        json_data = {'position': {'x': x, 'y': y}}
        json_data = {'position': [x, y, z]} # 3D Plan
        json_data = {'position': {'x': x, 'y': y, 'z': z}}

    or a GPS geo-location point :py:class:`sp.core.geometry.point.gps.GpsPoint`

    .. code-block:: python

        latitude, longitude = 37.70876818399, -122.51256379510176
        json_data = {'position': {'lat': latitude, 'lon': longitude}}

    The resource costs are loaded as a polynomial, linear or constant function
    using the :py:mod:`sp.core.estimator.polynomial` module

    E.g.:

    .. code-block:: python

        json_data = {
            'id': 0,
            'type': 'BS',
            'avail': 0.9,

            # f(x) = 20 + (50 - 20)x
            'power': [20, 50],

            # x = 0, y = 11
            'position': [0, 11],
            'capacity': {
                'CPU': 40,
                'RAM': 4000,
                'DISK': 16000
            },
            'cost': {
                # Polynomial cost: f(x) = 3x^2 + 10x + 5
                'CPU': [3, 10, 5],

                # Linear cost: f(x) = 2x + 30
                'RAM': [2, 30],

                # Constant cost f(x) = 20
                'DISK': 20
            }
        }
        node = sp.core.model.node.from_json(json_data)

    Args:
        json_data (dict): data loaded from a json
    Returns:
        Node: loaded node
    Raises:
        KeyError: Attribute not found
    """

    node = Node()
    node.id = int(json_data["id"])
    node.type = str(json_data["type"]).upper()
    node.availability = float(json_data["avail"])
    node.power_consumption = power.from_json(json_data["power"])
    node.position = point.from_json(json_data["position"])

    for (resource, value) in iteritems(json_data["capacity"]):
        node.capacity[resource] = float(value)

    for (resource, value) in iteritems(json_data["cost"]):
        resource = str(resource).upper()
        estimator = polynomial.from_json(value)
        node.cost[resource] = estimator

    return node
