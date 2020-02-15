class Scenario:
    CACHE_APPS_KEY = "apps"
    CACHE_USERS_KEY = "users"
    CACHE_RESOURCES_KEY = "resources"

    def __init__(self):
        self.topology = None
        self._apps = {}
        self._users = {}
        self._resources = {}
        self._cache = {}

    @property
    def nodes(self):
        return self.topology.nodes

    @property
    def apps(self):
        if self.CACHE_APPS_KEY not in self._cache:
            data = list(self._apps.values())
            data.sort()
            self._cache[self.CACHE_APPS_KEY] = data
        return self._cache[self.CACHE_APPS_KEY]

    @property
    def users(self):
        if self.CACHE_USERS_KEY not in self._cache:
            data = list(self._users.values())
            self._cache[self.CACHE_USERS_KEY] = data
        return self._cache[self.CACHE_USERS_KEY]

    @property
    def resources(self):
        if self.CACHE_RESOURCES_KEY not in self._cache:
            data = list(self._resources.values())
            self._cache[self.CACHE_RESOURCES_KEY] = data
        return self._cache[self.CACHE_RESOURCES_KEY]

    @property
    def cloud_node(self):
        return self.topology.cloud_node

    def get_node(self, node_id):
        return self.topology.get_node(node_id)

    def get_app(self, app_id):
        return self._apps[app_id]

    def get_user(self, user_id):
        return self._users[user_id]

    def get_resource(self, resource_name):
        return self._resource[resource_name]

    def get_nb_users(self, app_id, node_id):
        count = 0
        for user in self.users:
            if user.app_id == app_id and user.node_id == node_id:
                count += 1
        return count
