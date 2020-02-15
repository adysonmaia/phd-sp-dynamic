from .resource import Resource


class Topology:
    CACHE_NODES_KEY = "nodes"
    CACHE_LINKS_KEY = "links"
    CACHE_CLOUD_KEY = "cloud"
    CACHE_BS_KEY = "bs"

    def __init__(self):
        self.graph = None
        self._nodes = {}
        self._links = {}
        self._cache = {}

    def _clean_cache(self):
        self.__cache = {}

    @property
    def nodes(self):
        if self.CACHE_NODES_KEY not in self._cache:
            data = list(self._nodes.values())
            data.sort()
            self._cache[self.CACHE_NODES_KEY] = data
        return self._cache[self.CACHE_NODES_KEY]

    @property
    def links(self):
        if self.CACHE_LINKS_KEY not in self._cache:
            data = list(self._links.values())
            self._cache[self.CACHE_LINKS_KEY] = data
        return self._cache[self.CACHE_LINKS_KEY]

    @property
    def cloud_node(self):
        if self.CACHE_CLOUD_KEY not in self._cache:
            for node in self.nodes:
                if node.is_cloud():
                    self._cache[self.CACHE_CLOUD_KEY] = node
                    break
        return self._cache[self.CACHE_CLOUD_KEY]

    def get_node(self, node_id):
        return self._nodes[node_id]

    def get_nodes_by_type(self, type):
        return list(filter(lambda i: i.type == type, self.nodes))

    def get_bs_nodes(self):
        if self.CACHE_BS_KEY not in self._cache:
            self._cache[self.CACHE_BS_KEY] = self.get_nodes_by_type(Node.BS_TYPE)
        return self._cache[self.CACHE_BS_KEY]

    def get_link(self, src_node_id, dst_node_id):
        key_1 = (src_node_id, dst_node_id)
        key_2 = key_1[::-1]
        if key_1 in self._links:
            return self._links[key_1]
        elif key_2 in self._links:
            return self._links[key_2]
        else:
            raise KeyError("link (%d,%d) not found" % (src_node_id, dst_node_id))

    def add_node(self, node):
        self._nodes[node.id] = node
        self._clean_cache()

    def add_link(self, link):
        self._links[link.nodes_id] = link
        self._clean_cache()


class Node:
    BS_TYPE = "BS"
    CORE_TYPE = "CORE"
    CLOUD_TYPE = "CLOUD"
    POWER_IDLE = "idle"
    POWER_MAX = "max"
    K1 = "a"
    K2 = "b"

    def __init__(self):
        self._id = -1
        self._type = ""
        self._availability = 0
        self._power_consumption = {}
        self._capacity = {}
        self._cost = {}
        self._position = None

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = int(value)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = str(value).upper()

    @property
    def availability(self):
        return self._availability

    @availability.setter
    def availability(self, value):
        self._availability = float(value)

    @property
    def power_consumption(self):
        value = self._power_consumption
        return value[self.POWER_IDLE], value[self.POWER_MAX]

    @power_consumption.setter
    def power_consumption(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            self._power_consumption = {
                self.POWER_IDLE: float(value[0]),
                self.POWER_MAX: float(value[1])
            }
        elif isinstance(value, dict):
            self._power_consumption = {
                self.POWER_IDLE: float(value[self.POWER_IDLE]),
                self.POWER_MAX: float(value[self.POWER_MAX])
            }
        else:
            raise TypeError

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            self._position = [float(value[0]), float(value[1])]
        elif isinstance(value, dict):
            self._position = [value["x"], value["y"]]
        else:
            raise TypeError

    def get_capacity(self, resource_name):
        return self._capacity[resource_name]

    def set_capacity(self, resource_name, value):
        resource_name = str(resource_name).upper()
        value = float(value)
        self._capacity[resource_name] = value

    def get_cpu_capacity(self):
        return self._capacity[Resource.CPU]

    def get_cost(self, resource_name):
        value = self._cost[resource_name]
        return value[self.K1], value[self.K2]

    def set_cost(self, resource_name, value):
        resource_name = str(resource_name).upper()
        if isinstance(value, list) or isinstance(value, tuple):
            self._cost[resource_name] = {
                self.K1: float(value[0]),
                self.K2: float(value[1])
            }
        elif isinstance(value, dict):
            self._cost[resource_name] = {
                self.K1: float(value[self.K1]),
                self.K2: float(value[self.K2])
            }
        else:
            raise TypeError

    def is_base_station(self):
        return self.type == self.BS_TYPE

    def is_core(self):
        return self.type == self.CORE_TYPE

    def is_cloud(self):
        return self.type == self.CLOUD_TYPE


class Link:
    def __init__(self):
        self._nodes_id = (-1,-1)
        self._bandwidth = 0
        self._propagation_delay = 0

    def __eq__(self, other):
        ids_1 = self.nodes_id
        ids_2 = other.nodes_id
        ids_3 = ids_2[::-1]
        return (ids_1 == ids_2) or (ids_1 == ids_3)

    @property
    def nodes_id(self):
        return self._nodes_id

    @nodes_id.setter
    def nodes_id(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            self._nodes_id = (int(value[0]), int(value[1]))
        elif isinstance(value, dict):
            self._nodes_id = (int(value["s"]), int(value["d"]))
        else:
            raise TypeError

    @property
    def bandwidth(self):
        return self._bandwidth

    @bandwidth.setter
    def bandwidth(self, value):
        self._bandwidth = float(value)

    @property
    def propagation_delay(self):
        return self._propagation_delay

    @propagation_delay.setter
    def propagation_delay(self, value):
        self._propagation_delay = float(value)
