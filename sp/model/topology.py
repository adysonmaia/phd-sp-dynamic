from .node import Node
from .link import Link
from  sp.utils import json_util
import networkx as nx


class Topology:
    CACHE_NODES_KEY = "nodes"
    CACHE_LINKS_KEY = "links"
    CACHE_CLOUD_KEY = "cloud"
    CACHE_BS_KEY = "bs"

    def __init__(self):
        self.graph = nx.Graph()
        self._nodes = {}
        self._links = {}
        self._cache = {}

    def _clean_cache(self):
        self._cache.clear()

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

    @property
    def bs_nodes(self):
        if self.CACHE_BS_KEY not in self._cache:
            self._cache[self.CACHE_BS_KEY] = self.get_nodes_by_type(Node.BS_TYPE)
        return self._cache[self.CACHE_BS_KEY]

    def get_node(self, node_id):
        return self._nodes[node_id]

    def get_nodes_by_type(self, type):
        return list(filter(lambda i: i.type == type, self.nodes))

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
        self.graph.add_node(node.id)
        self._nodes[node.id] = node
        self._clean_cache()

    def add_link(self, link):
        self.graph.add_edge(*link.nodes_id)
        self._links[link.nodes_id] = link
        self._clean_cache()

    @classmethod
    def from_json(cls, json_data):
        return from_json(json_data)


def from_json(json_data):
    t = Topology()

    for item in json_util.load_key_content(json_data, "nodes"):
        node = Node.from_json(item)
        t.add_node(node)

    for item in json_util.load_key_content(json_data, "links"):
        link = Link.from_json(item)
        t.add_link(link)

    return t

