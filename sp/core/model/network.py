from .node import Node
from .link import Link
from sp.core.utils import json_util
from sp.core.libs.cached_property import cached_property


class Network:
    """Network Class Model
    It is store the network graph and its properties
    A network graph is composed of Nodes (:py:class:`sp.core.model.Node`) and Links (:py:class:`sp.core.model.Link`)

    This class follows an Edge Computing topology for mobile networks that usually have three parts:
    Access Network <--> Core Network <--> Cloud Network
    * The access network is composed of base stations acting as access points and computing host (edge nodes).
    The access network is connected to the core network or to the cloud network
    * The core network is an optional part that represents the core of a mobile network
    * The cloud network is composed of one single node representing a large cloud data center

    """
    def __init__(self):
        """Initialization
        """
        self._nodes = {}
        self._links = {}

    def _clear_cache(self):
        """Clear the cached properties
        """
        keys = ["nodes", "links", "cloud_node"]
        for key in keys:
            if key in self.__dict__:
                del self.__dict__[key]

    @cached_property
    def nodes(self):
        """List of all node in the network
        Returns:
            list(Node): list of nodes
        """
        data = list(self._nodes.values())
        data.sort()
        return data

    @cached_property
    def links(self):
        """List of all links in the network
        Returns:
            list(Link): list of links
        """
        return list(self._links.values())

    @cached_property
    def cloud_node(self):
        """The cloud node of the network
        Returns:
             Node: cloud node
        """
        for node in self.nodes:
            if node.is_cloud():
                return node

        raise AttributeError("Cloud node not found")

    @property
    def nodes_id(self):
        """List of ids of all nodes
        Returns:
           list: list of ids
        """
        return self._nodes.keys()

    @property
    def bs_nodes(self):
        """List of all base station nodes
        Returns:
           list(Node): list of nodes
        """
        return self.get_nodes_by_type(Node.BS_TYPE)

    def get_node(self, node_id):
        """"Get a node by its id
        Args:
            node_id (int): node's id
        Returns:
            Node: node
        Raises:
            KeyError: no node found for the specified id
        """
        return self._nodes[node_id]

    def get_nodes_by_type(self, node_type):
        """"Get a list of nodes with a specific type
        Args:
           node_type (str): type of the node
        Returns:
           list(Node): nodes
        """
        return list(filter(lambda i: i.type == node_type, self.nodes))

    def get_link(self, src_node_id, dst_node_id):
        """"Get a link by its vertices (nodes)
        A link is an undirected edge of the network graph

        Args:
            src_node_id (int): a vertex of the link
            dst_node_id (int): other vertex of the link
        Returns:
            Link: link between the two specified nodes
        Raises:
            KeyError: link not found between the nodes
        """
        key_1 = (src_node_id, dst_node_id)
        key_2 = key_1[::-1]
        if key_1 in self._links:
            return self._links[key_1]
        elif key_2 in self._links:
            return self._links[key_2]
        else:
            raise KeyError("link (%d,%d) not found" % (src_node_id, dst_node_id))

    def link_exists(self, src_node_id, dst_node_id):
        """Check if exists a link between two nodes
        Args:
            src_node_id (int): node's id
            dst_node_id (int): other node's id
        Returns:
            bool: whether link exists or not
        """
        key_1 = (src_node_id, dst_node_id)
        key_2 = key_1[::-1]
        return key_1 in self._links or key_2 in self._links

    def add_node(self, node):
        """Add a node to the network
        Args:
            node (Node): new node
        """
        self._nodes[node.id] = node
        self._clear_cache()

    def add_link(self, link):
        """Add a link to the network
        Args:
            link (Link): new link
        """
        self._links[link.nodes_id] = link
        self._clear_cache()

    @staticmethod
    def from_json(json_data):
        """Create a Network object from a json data
        See :py:func:`sp.core.model.network.from_json`
        Args:
            json_data (dict): data loaded from a json
        Returns:
            Network: loaded network
        """
        return from_json(json_data)


def from_json(json_data):
    """Create a Network object from a json data
    The nodes and links data can be placed directly inside the json data or in external json files

    See :py:func:`sp.core.model.node.from_json` and :py:func:`sp.core.model.link.from_json`
    to have more detail about nodes and links specifications

    E.g.:

    .. code-block:: python

        # Nodes and links properties inside the json data
        json_data = {
            'nodes': [
                {'id':  0, 'type':  'CLOUD', ...},
                {'id':  1, 'type':  'CORE', ...},
                {'id':  2, 'type':  'BS', ...},
                {'id':  3, 'type':  'BS', ...}
            ],
            'links': [
                {'nodes':  [0, 1], 'bw':  2e+10, 'delay':  10.0},
                {'nodes':  [1, 2], 'bw':  1e+10, 'delay':  1.0},
                {'nodes':  [1, 3], 'bw':  1e+10, 'delay':  1.0},
                {'nodes':  [2, 3], 'bw':  1e+10, 'delay':  1.4}
            ]
        }
        net = sp.core.model.network.from_json(json_data)

        # Nodes and links properties in external json files
        json_data = {
            'nodes': 'path/nodes.json',
            'links': 'path/links.json'
        }
        net = sp.core.model.network.from_json(json_data)

    Args:
        json_data (dict): data loaded from a json
    Returns:
        Network: loaded network
    Raises:
        KeyError: Attributes not found
    """
    net = Network()

    for item in json_util.load_key_content(json_data, "nodes"):
        node = Node.from_json(item)
        net.add_node(node)

    for item in json_util.load_key_content(json_data, "links"):
        link = Link.from_json(item)
        net.add_link(link)

    return net

