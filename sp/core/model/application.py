from sp.core.model import Resource
from sp.core.estimator import polynomial
from future.utils import iteritems
from functools import total_ordering


@total_ordering
class Application:
    """ Application Model Class
    it is used to store requirements and properties of an application

    Attributes:
        id (int): Unique identification of the application
        type (str): String used to classify applications in groups. E.g., 5G apps use cases: EMBB, URLLC, MMTC
        deadline (float): Maximum time (time units) allowed for responding a request for the application
        work_size (float): Amount of CPU (instructions) required to get a response to a request
        data_size (float): Data size of an request (bits or bytes) transmitted on the network
        request_rate (float): Request generation rate (requests per time unit) of each user requesting this application
        max_instances (int): Max. number of nodes allowed to host the application, value >= 1
        availability (float): Probability that an application instance is working without failure, 0 <= value <= 1
        demand (dict): For each resource, it specifies a function to calculate the amount of resources required
            by an application instance with a certain workload.

            The dictionary's keys are the resource names and the values are
            estimator :py:class:`sp.core.estimator.Estimator` objects.
            Call :py:meth:`sp.core.estimator.Estimator.calc` to obtain the required amount of resource.
            E.g. code-block:: python

                resource_name = 'CPU'
                workload = 1
                app.demand[resource_name](workload)

    """

    def __init__(self):
        """ Initialization
        """
        self.id = -1
        self.type = ""
        self.deadline = 0.0
        self.work_size = 0.0
        self.data_size = 0.0
        self.request_rate = 0.0
        self.max_instances = 0
        self.availability = 0.0
        self.demand = {}

    def __eq__(self, other):
        """ Compare if two applications are equals by their ids
        """
        return self.id == other.id

    def __lt__(self, other):
        """ Use the id attribute in the < operator
        """
        return self.id < other.id

    @property
    def cpu_demand(self):
        """Get the CPU demand estimator
        Returns:
            sp.core.estimator.Estimator: The demand estimator
        Raises:
            KeyError: Resource not found
        """
        return self.demand[Resource.CPU]

    def get_demand(self, resource_name):
        """Get the demand estimator for a specific resource
        Args:
            resource_name (str): name of the resource
        Returns:
            sp.core.estimator.Estimator: The demand estimator
        Raises:
            KeyError: Resource not found
        """
        return self.demand[resource_name]

    @staticmethod
    def from_json(json_data):
        """Create an application object from a json data
        See :py:func:`sp.core.model.application.from_json`
        Args:
            json_data (dict): data loaded from a json
        Returns:
            Application: loaded application
        """
        return from_json(json_data)


def from_json(json_data):
    """Create an application object from a json data.
    The resource demands are loaded as a polynomial, linear or constant function
    using the :py:module:`sp.core.estimator.polynomial` module

    E.g. code-block:: python

        json_data = {
            'id': 0,
            'type': 'MMTC',
            'deadline': 1,
            'work': 1,
            'data': 1.
            'rate': 1,
            'avail': 0.99,
            'max_inst': 100,
            'demand': {
                'CPU': [3, 10, 5],  # Polynomial demand: f(x) = 3x^2 + 10x + 5
                'RAM': [2, 30],     # Linear demand: f(x) = 2x + 30
                'DISK': 20          # Constant demand f(x) = 20
            }
        }

        app = sp.core.model.application.from_json(json_data)

    Args:
        json_data (dict): data loaded from a json
    Returns:
        Application: loaded application
    Raises:
        KeyError: Application's attributes not found
    """

    app = Application()
    app.id = int(json_data["id"])
    app.type = str(json_data["type"]).upper()
    app.deadline = float(json_data["deadline"])
    app.work_size = float(json_data["work"])
    app.data_size = float(json_data["data"])
    app.request_rate = float(json_data["rate"])
    app.availability = float(json_data["avail"])
    app.max_instances = int(json_data["max_inst"])
    for resource, value in iteritems(json_data["demand"]):
        resource = str(resource).upper()
        estimator = polynomial.from_json(value)
        app.demand[resource] = estimator

    return app
