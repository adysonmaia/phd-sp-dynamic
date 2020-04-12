from .resource import Resource
from .network import Network
from .application import Application
from .user import User
from sp.core.utils import json_util
from sp.core.libs.cached_property import cached_property


class Scenario:
    """Scenario Model Class
    It is used to store the scenario that will be used in the simulation
    A scenario is composed of the network, applications, users, and resources
    """
    def __init__(self):
        """Initialization
        """
        self._network = None
        self._apps = {}
        self._users = {}
        self._resources = {}

    def _clear_cache(self):
        """Clear the cached properties
        """
        keys = ["apps", "users", "resources"]
        for key in keys:
            if key in self.__dict__:
                del self.__dict__[key]

    @cached_property
    def apps(self):
        """List of all applications in the scenario
        Returns:
            list(Application): applications
        """
        data = list(self._apps.values())
        data.sort()
        return data

    @cached_property
    def users(self):
        """List of all users in the scenario
        Returns:
            list(User): users
        """
        return list(self._users.values())

    @cached_property
    def resources(self):
        """List of all resources in the scenario
        Returns:
            list(Resource): resources
        """
        return list(self._resources.values())

    @property
    def network(self):
        """Get network of the scenario
        Returns:
            Network: scenario's network
        """
        return self._network

    @network.setter
    def network(self, value):
        """Set network of the scenario
        """
        self._network = value
        self._clear_cache()

    @property
    def apps_id(self):
        """Get id of all applications
        Returns:
            list(int): list of ids
        """
        return self._apps.keys()

    @property
    def users_id(self):
        """Get id of all users
        Returns:
            list(int): list of ids
        """
        return self._users.keys()

    @property
    def resources_name(self):
        """Get all types of resources
        Returns:
            list(str): name of each resource type
        """
        return self._resources.keys()

    def add_app(self, app):
        """Add an application in the scenario
        Args:
            app (Application): new application
        """
        self._apps[app.id] = app
        self._clear_cache()

    def get_app(self, app_id):
        """Get an application by its id
        Args:
            app_id (int): application's id
        Returns:
            Application: application
        Raises:
            KeyError: no application found for the specified id
        """
        return self._apps[app_id]

    def get_user(self, user_id):
        """Get a user by its id
        Args:
            user_id (int): user's id
        Returns:
            User: user
        Raises:
            KeyError: no user found for the specified id
        """
        return self._users[user_id]

    def add_user(self, user):
        """Add a user in the scenario
        Args:
            user (User): new user
        """
        self._users[user.id] = user
        self._clear_cache()

    def get_resource(self, resource_name):
        """Get a resource bt its type/name
        Args:
            resource_name (str): name of the resource type
        Returns:
            Resource: resource
         Raises:
            KeyError: no resource found with the specified name
        """
        return self._resources[resource_name]

    def add_resource(self, resource):
        """Add a resource in the scenario
        Args:
            resource (Resource): new resource
        """
        self._resources[resource.name] = resource
        self._clear_cache()

    @staticmethod
    def from_json(json_data):
        """Create a Scenario object from a json data
        See :py:func:`sp.core.model.scenario.from_json`
        Args:
            json_data (dict): data loaded from a json
        Returns:
            Scenario: loaded scenario
        Raises:
            KeyError: attribute not found
        """
        return from_json(json_data)


def from_json(json_data):
    """Create a Scenario object from a json data
    Each scenario properties (resources, network, apps, and users) can be directly passed inside the json data
        or as external json files
    If the resources is not informed, it is inferred through the properties of the network nodes

    See the following functions to more details about scenario's properties specifications
    * :py:func:`sp.core.model.resource.from_json`
    * :py:func:`sp.core.model.network.from_json`
    * :py:func:`sp.core.model.application.from_json`
    * :py:func:`sp.core.model.user.from_json`

    E.g.:

    .. code-block:: python

        # Scenario's properties inside the json data
        json_data = {
            'nodes': [
                {'id':  0, 'type':  'CLOUD', ...},
                {'id':  1, 'type':  'CORE', ...},
                {'id':  2, 'type':  'BS', ...},
                {'id':  3, 'type':  'BS', ...}
            ],
            'links': [
                {'nodes':  [0, 1], ...},
                {'nodes':  [1, 2], ...},
                {'nodes':  [1, 3], ...},
                {'nodes':  [2, 3], ...}
            ],
            'apps': [
                {'id':  0, 'type':  'EMBB', ...},
                {'id':  1, 'type':  'URLLC', ...},
                {'id':  2, 'type':  'MMTC', ...}
            ],
            'users': [
                {'id':  0, 'app_id':  0, ...},
                {'id':  1, 'app_id':  1, ...},
                {'id':  2, 'app_id':  2, ...},
                {'id':  3, 'app_id':  0, ...}
            ]
        }
        scenario = sp.core.model.scenario.from_json(json_data)

        # Scenario's properties in external json files
        json_data = {
            'network': 'path/network.json',
            'apps': 'path/apps.json',
            'users': 'path/users.json',
            'resources': 'path/resources.json'
        }
        scenario = sp.core.model.scenario.from_json(json_data)

    Args:
        json_data:
    Returns:
         Scenario: loaded scenario
    Raises:
        KeyError: attribute not found
    """
    s = Scenario()

    network_data = json_data
    if "network" in json_data:
        network_data = json_util.load_key_content(json_data, "network")
    s.network = Network.from_json(network_data)

    if "resources" in json_data:
        for item in json_util.load_key_content(json_data, "resources"):
            r = Resource.from_json(item)
            s.add_resource(r)
    else:
        for resource_name in s.network.cloud_node.capacity.keys():
            r = Resource()
            r.name = resource_name
            s.add_resource(r)

    for item in json_util.load_key_content(json_data, "apps"):
        app = Application.from_json(item)
        s.add_app(app)

    for item in json_util.load_key_content(json_data, "users"):
        user = User.from_json(item)
        s.add_user(user)

    return s

