from . import Routing
from sp.estimator.link_delay import DefaultLinkDelayEstimator
from sp.utils import floyd_warshall


class ShortestPathRouting(Routing):
    def __init__(self, system=None):
        Routing.__init__(self, system)
        self.static_routing = True
        self.link_delay_estimator = None

        self.paths = None
        self.distances = None

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

        if self.link_delay_estimator is None:
            self.link_delay_estimator = DefaultLinkDelayEstimator(self.system)
        self.link_delay_estimator.system = self.system

        graph = self.system
        self.distances = {}
        self.paths = {}
        for app in self.system.apps:
            # TODO: improve this part because the shortest paths are the same for all applications
            succ, dist = floyd_warshall.run(graph, lambda s, d: self.link_delay_estimator.calc(app.id, s, d))
            self.distances[app.id] = dist
            self.paths[app.id] = floyd_warshall.reconstruct_all_paths(graph, succ)




