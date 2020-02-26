from .node import Node
from .link import Link
from sp.core.utils import json_util
from sp.core.libs.cached_property import cached_property


class Topology:
    def __init__(self):
        self._nodes = {}
        self._links = {}

    def _clean_cache(self):
        keys = ["nodes", "links", "cloud_node"]
        for key in keys:
            if key in self.__dict__:
                del self.__dict__[key]

    @cached_property
    def nodes(self):
        data = list(self._nodes.values())
        data.sort()
        return data

    @cached_property
    def links(self):
        return list(self._links.values())

    @cached_property
    def cloud_node(self):
        for node in self.nodes:
            if node.is_cloud():
                return node

        raise AttributeError("Cloud node not found")

    @property
    def nodes_id(self):
        return self._nodes.keys()

    @property
    def bs_nodes(self):
        return self.get_nodes_by_type(Node.BS_TYPE)

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

    def link_exists(self, src_node_id, dst_node_id):
        key_1 = (src_node_id, dst_node_id)
        key_2 = key_1[::-1]
        return key_1 in self._links or key_2 in self._links

    def add_node(self, node):
        self._nodes[node.id] = node
        self._clean_cache()

    def add_link(self, link):
        self._links[link.nodes_id] = link
        self._clean_cache()

    @staticmethod
    def from_json(json_data):
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

