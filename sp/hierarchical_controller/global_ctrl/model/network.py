from sp.core.model.network import Network
from sp.core.model.link import Link
from sp.physical_system.util import floyd_warshall
from .node import GlobalNode
import math


class GlobalNetwork(Network):
    """Global Network

    Attributes:
        real_network(Network): real network
    """

    def __init__(self):
        """Initialization
        """

        Network.__init__(self)
        self.real_network = None

    @staticmethod
    def from_real_network(network, clusters):
        """Create a network of subsystems/clusters

        Args:
            network (Network): real network
            clusters (list(list)): list of clusters. Each cluster as a subsystem is a list containing nodes' id

        Returns:
           GlobalNetwork: global network
        """
        return from_real_network(network, clusters)


def from_real_network(network, clusters):
    """Create a network of subsystems/clusters

    Args:
        network (Network): real network
        clusters (list(list)): list of clusters. Each cluster as a subsystem is a list containing nodes' id

    Returns:
       GlobalNetwork: global network
    """
    global_net = GlobalNetwork()
    global_net.real_network = network

    last_id = max(network.nodes_id)
    for real_nodes_id in clusters:
        global_node = GlobalNode()
        for real_node_id in real_nodes_id:
            real_node = network.get_node(real_node_id)
            global_node.add_node(real_node)
        if len(global_node.nodes) > 0:
            last_id += 1
            global_node.id = last_id
            global_node.type = global_node.nodes[0].type
            global_net.add_node(global_node)

    for src_global_node in global_net.nodes:
        for dst_global_node in global_net.nodes:
            link_exists = False
            for src_real_node in src_global_node.nodes:
                for dst_real_node in dst_global_node.nodes:
                    if network.link_exists(src_real_node.id, dst_real_node.id):
                        link_exists = True
                        break
            if link_exists:
                # TODO: define the bandwidth and propagation delay
                global_link = Link()
                global_link.nodes_id = (src_global_node.id, dst_global_node.id)
                global_net.add_link(global_link)

    global_net = _obtain_central_nodes(network, global_net)

    return global_net


def _obtain_central_nodes(real_net, global_net):
    """Obtain central node of each cluster

    Args:
        real_net (Network): real network
        global_net (GlobalNetwork): global network comprising of cluster nodes

    Returns:
        Network: updated subsystems network
    """
    succ, dist = floyd_warshall.run(real_net, _get_link_weight)
    for global_node in global_net.nodes:
        central_node = None
        central_delay = math.inf
        for src_real_node in global_node.nodes:
            delay = sum(map(lambda n: dist[src_real_node.id][n.id], global_node.nodes))
            if delay < central_delay:
                central_node = src_real_node
                central_delay = delay
        global_node.central_node = central_node
    return global_net


def _get_link_weight(graph, src_node_id, dst_node_id):
    """Get weight of each link

    Args:
        graph: graph
        src_node_id: a node of the link
        dst_node_id: another node of the link

    Returns:
        float: link's weight
    """
    if graph.link_exists(src_node_id, dst_node_id):
        link = graph.get_link(src_node_id, dst_node_id)
        return link.propagation_delay + (1.0 / float(link.bandwidth))
    else:
        return math.inf
