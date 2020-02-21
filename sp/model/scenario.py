from .resource import Resource
from .topology import Topology
from .application import Application
from .user import User
from sp.utils import json_util


class Scenario:
    CACHE_APPS_KEY = "apps"
    CACHE_USERS_KEY = "users"
    CACHE_RESOURCES_KEY = "resources"

    def __init__(self):
        self._topology = None
        self._apps = {}
        self._users = {}
        self._resources = {}
        self._cache = {}

    def _clean_cache(self):
        self._cache.clear()

    @property
    def topology(self):
        return self._topology

    @topology.setter
    def topology(self, value):
        self._topology = value
        self._clean_cache()

    @property
    def apps(self):
        if self.CACHE_APPS_KEY not in self._cache:
            data = list(self._apps.values())
            data.sort()
            self._cache[self.CACHE_APPS_KEY] = data
        return self._cache[self.CACHE_APPS_KEY]

    @property
    def apps_id(self):
        return self._apps.keys()

    @property
    def users(self):
        if self.CACHE_USERS_KEY not in self._cache:
            data = list(self._users.values())
            self._cache[self.CACHE_USERS_KEY] = data
        return self._cache[self.CACHE_USERS_KEY]

    @property
    def users_id(self):
        return self._users.keys()

    @property
    def resources(self):
        if self.CACHE_RESOURCES_KEY not in self._cache:
            data = list(self._resources.values())
            self._cache[self.CACHE_RESOURCES_KEY] = data
        return self._cache[self.CACHE_RESOURCES_KEY]

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
        return self._resource[resource_name]

    def add_resource(self, resource):
        self._resources[resource.name] = resource
        self._clean_cache()

    @classmethod
    def from_json(cls, json_data):
        return from_json(json_data)


def _json_key_content(json_data, key):
    if key not in json_data:
        raise TypeError

    item = json_data[key]
    if isinstance(item, str):
        import json
        with open(item) as json_file:
            return json.load(json_file)
    else:
        return item


def from_json(json_data):
    s = Scenario()

    topology_data = json_data
    if "topology" in json_data:
        topology_data = json_util.load_key_content(json_data, "topology")
    s.topology = Topology.from_json(topology_data)

    if "resources" in json_data:
        for item in json_util.load_key_content(json_data, "resources"):
            r = Resource.from_json(item)
            s.add_resource(r)
    else:
        for resource_name in s.topology.cloud_node.capacity.keys():
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

