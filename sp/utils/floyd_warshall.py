from collections import defaultdict


def run(graph, weight_func=None):
    return floyd_warshall(graph, weight_func)


def floyd_warshall(graph, weight_func=None):
    if weight_func is None:
        weight_func = default_link_weight
    dist = defaultdict(lambda: defaultdict(lambda: float('inf')))

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
    return 1.0


def reconstruct_path(src_node_id, dst_node_id, successors):
    if src_node_id not in successors or dst_node_id not in successors[src_node_id]:
        return []
    u, v = src_node_id, dst_node_id
    path = [u]
    while u != v:
        u = successors[u][v]
        path.append(u)
    return path


def reconstruct_all_paths(graph, successors):
    paths = defaultdict(dict)
    nodes_id = graph.nodes_id
    for u in nodes_id:
        for v in nodes_id:
            paths[u][v] = reconstruct_path(u, v, successors)
    return dict(paths)
