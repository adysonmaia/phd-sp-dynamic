from .resource import Resource
from .network import Network
from .application import Application
from .user import User
from sp.core.utils import json_util
from sp.core.libs.cached_property import cached_property


class Scenario:
    def __init__(self):
        self._network = None
        self._apps = {}
        self._users = {}
        self._resources = {}

    def _clean_cache(self):
        keys = ["apps", "users", "resources"]
        for key in keys:
            if key in self.__dict__:
                del self.__dict__[key]

    @cached_property
    def apps(self):
        data = list(self._apps.values())
        data.sort()
        return data

    @cached_property
    def users(self):
        return list(self._users.values())

    @cached_property
    def resources(self):
        return list(self._resources.values())

    @property
    def network(self):
        return self._network

    @network.setter
    def network(self, value):
        self._network = value
        self._clean_cache()

    @property
    def apps_id(self):
        return self._apps.keys()

    @property
    def users_id(self):
        return self._users.keys()

    @property
    def resources_name(self):
        return self._resources.keys()

    def add_app(self, app):
        self._apps[app.id] = app
        self._clean_cache()

    def get_app(self, app_id):
        return self._apps[app_id]

    def get_user(self, user_id):
        return self._users[user_id]

    def add_user(self, user):
        self._users[user.id] = user
        self._clean_cache()

    def get_resource(self, resource_name):
        return self._resources[resource_name]

    def add_resource(self, resource):
        self._resources[resource.name] = resource
        self._clean_cache()

    @staticmethod
    def from_json(json_data):
        return from_json(json_data)


def from_json(json_data):
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

