from . import Routing
from sp.estimator.link_delay import DefaultLinkDelayEstimator
from collections import defaultdict


class ShortestPathRouting(Routing):
    def __init__(self, system=None):
        Routing.__init__(self, system)
        self.static_routing = True
        self.paths = None
        self.distances = None
        self.estimator = None

    def get_path(self, app_id, src_node_id, dst_node_id):
        return self.paths[app_id][src_node_id][dst_node_id]

    def get_path_length(self, app_id, src_node_id, dst_node_id):
        return self.distances[app_id][src_node_id][dst_node_id]

    def get_all_paths(self):
        return self.paths

    def get_all_paths_length(self):
        return self.distances

    def update(self, time):
        if self.static_routing and self.paths is not None:
            return

        if self.estimator is None:
            self.estimator = DefaultLinkDelayEstimator(self.system)
        else:
            self.estimator.system = self.system

        graph = self.system
        self.distances = {}
        self.paths = {}
        for app in self.system.apps:
            # TODO: improve this part because the shortest paths are the same for all applications
            succ, dist = floyd_warshall(graph, lambda s, d: self.estimator.calc(app.id, s, d))
            self.distances[app.id] = dist
            self.paths[app.id] = reconstruct_all_paths(graph, succ)


def default_link_weight(src_node_id, dst_node_id):
    return 1.0


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
        l_weight = weight_func(u, v)
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

