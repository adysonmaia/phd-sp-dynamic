from collections import defaultdict
import math


def run(graph, weight_func=None):
    """Execute Floyd–Warshall Algorithm.

    See :py:func:`sp.physical_system.util.floyd_warshall.floyd_warshall`

    Args:
        graph: undirected graph
        weight_func (function): link/edge weight function

    Returns:
        (dict, dict): successors and minimum distance matrices
    """
    return floyd_warshall(graph, weight_func)


def floyd_warshall(graph, weight_func=None):
    """Floyd–Warshall Shortest Path Algorithm

    See Also: https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm

    E.g.:

    .. code-block:: python

            successors, distances = floyd_warshall(graph)
            u, v = 0, 1
            distance_uv = distances[u][v]
            successor_uv = successors[u][v]
            path_uv = reconstruct_path(u, v, successors)

    Args:
        graph: undirected graph. It needs to have nodes_id and links properties
        weight_func (function): it specifies the (positive) weight of each link/edge in the graph.
            If none, each link has the weight equal to 1.0
    Returns:
        (dict, dict): successors and minimum distance matrices
    """
    if weight_func is None:
        weight_func = default_link_weight
    dist = defaultdict(lambda: defaultdict(lambda: math.inf))

    nodes_id = graph.nodes_id
    for u in nodes_id:
        dist[u][u] = 0.0

    succ = defaultdict(dict)
    for link in graph.links:
        u, v = link.nodes_id
        l_weight = weight_func(graph, u, v)
        dist[u][v] = min(l_weight, dist[u][v])
        succ[u][v] = v

        dist[v][u] = dist[u][v]
        succ[v][u] = u

    for w in nodes_id:
        for u in nodes_id:
            for v in nodes_id:
                if dist[u][v] > dist[u][w] + dist[w][v]:
                    dist[u][v] = dist[u][w] + dist[w][v]
                    succ[u][v] = succ[u][w]

    return dict(succ), dict(dist)


def default_link_weight(graph, src_node_id, dst_node_id):
    """Set weight of each link to 1.0

    Args:
        graph: graph
        src_node_id: a node of the link
        dst_node_id: another node of the link

    Returns:
        float: link's weight
    """
    return 1.0


def reconstruct_path(src_node_id, dst_node_id, successors):
    """Reconstruct shortest path from the successors matrix

    Args:
        src_node_id: starting node
        dst_node_id: destination node
        successors (dict(dict)): successors matrix

    Returns:
        list: shortest path from src_node_id to dst_node_id
    """

    if src_node_id not in successors or dst_node_id not in successors[src_node_id]:
        return []
    u, v = src_node_id, dst_node_id
    path = [u]
    while u != v:
        u = successors[u][v]
        path.append(u)
    return path


def reconstruct_all_paths(graph, successors):
    """Reconstruct shortest path of each pair of nodes/vertices in the graph

    Args:
        graph: undirected graph
        successors (dict(dict)): successors matrix

    Returns:
        dict(dict): for each pair of nodes (u,v), it contains the shortest path as a list
    """

    paths = defaultdict(dict)
    nodes_id = graph.nodes_id
    for u in nodes_id:
        for v in nodes_id:
            paths[u][v] = reconstruct_path(u, v, successors)
    return dict(paths)
