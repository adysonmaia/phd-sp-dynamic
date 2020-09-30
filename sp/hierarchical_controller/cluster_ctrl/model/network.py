from sp.core.model import Network, Node
from sp.core.util.cached_property import cached_property
from sp.hierarchical_controller.global_ctrl.model import GlobalNetwork, GlobalNode


class ClusterNetwork(Network):
    """Cluster Network

    """

    def __init__(self):
        """Initialization
        """
        Network.__init__(self)
        self.real_network = None
        self._internal_nodes = {}
        self._external_nodes = {}

    def _clear_cache(self):
        """Clear the cached properties
        """
        Network._clear_cache(self)
        keys = ["internal_nodes", "external_nodes"]
        for key in keys:
            if key in self.__dict__:
                del self.__dict__[key]

    def _get_central_node(self, node_id):
        """Get central node if the id refers to a global node.
        If it refers to a real node, then it returns this real node

        Args:
            node_id (int): node's id

        Returns:
            Node: node
        """
        if node_id in self._external_nodes:
            node = self.get_node(node_id)
            if isinstance(node, GlobalNode):
                return node.central_node
        elif self.real_network is not None:
            node = self.real_network.get_node(node_id)
        else:
            node = self.get_node(node_id)

        return node

    def add_node(self, node):
        """Add a node to the network

        Args:
            node (Node): new node
        """
        Network.add_node(self, node)
        if isinstance(node, GlobalNode):
            self._external_nodes[node.id] = node
        else:
            self._internal_nodes[node.id] = node
        self._clear_cache()

    def add_link(self, link):
        """Add a link to the network

        Args:
            link (Link): new link
        """
        # All links are saved in the real network
        pass

    @cached_property
    def internal_nodes(self):
        """Get real nodes inside the cluster

        Returns:
            list(Node): real nodes
        """
        data = list(self._internal_nodes.values())
        data.sort()
        return data

    @cached_property
    def external_nodes(self):
        """Get external cluster nodes

        Returns:
            list(GlobalNode): cluster nodes
        """
        data = list(self._external_nodes.values())
        data.sort()
        return data

    @property
    def links(self):
        """List of all links in the real network

        Returns:
            list(Link): list of links
        """
        if self.real_network is None:
            return []
        else:
            return self.real_network.links

    def get_link(self, src_node_id, dst_node_id):
        """"Get a link by its vertices (nodes).
        A link is an undirected edge of the network graph

        Args:
            src_node_id (int): a vertex of the link
            dst_node_id (int): other vertex of the link
        Returns:
            Link: link between the two specified nodes
        Raises:
            KeyError: link not found between the nodes
        """
        src_real_node = self._get_central_node(src_node_id)
        dst_real_node = self._get_central_node(dst_node_id)
        if self.real_network is None:
            raise KeyError("link (%d,%d) not found" % (src_node_id, dst_node_id))
        else:
            return self.real_network.get_link(src_real_node.id, dst_real_node.id)

    def link_exists(self, src_node_id, dst_node_id):
        """Check if exists a link between two nodes

        Args:
            src_node_id (int): node's id
            dst_node_id (int): other node's id
        Returns:
            bool: whether link exists or not
        """
        try:
            src_real_node = self._get_central_node(src_node_id)
            dst_real_node = self._get_central_node(dst_node_id)
            if self.real_network is not None:
                return self.real_network.link_exists(src_real_node.id, dst_real_node.id)
        except KeyError:
            pass

        return False

    @staticmethod
    def from_global_network(global_net, global_node):
        """Create a cluster network from a global network

        Args:
            global_net (GlobalNetwork):  global network
            global_node (GlobalNode): global node representing the cluster

        Returns:
            ClusterNetwork: cluster network
        """
        return from_global_network(global_net, global_node)


def from_global_network(global_net, global_node):
    """Create a cluster network from a global network

    Args:
        global_net (GlobalNetwork):  global network
        global_node (GlobalNode): global node representing the cluster

    Returns:
        ClusterNetwork: cluster network
    """
    cluster_net = ClusterNetwork()
    cluster_net.real_network = global_net.real_network
    for real_node in global_node.nodes:
        cluster_net.add_node(real_node)
    for external_cluster in global_net.nodes:
        # TODO: filter the addition of external clusters based on a global control input
        if external_cluster != global_node:
            cluster_net.add_node(external_cluster)

    return cluster_net

