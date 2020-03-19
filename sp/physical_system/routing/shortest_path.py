from . import Routing
from sp.physical_system.estimator import DefaultLinkDelayEstimator
from sp.physical_system.utils import floyd_warshall


class ShortestPathRouting(Routing):
    def __init__(self):
        Routing.__init__(self)
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

    def update(self, system, environment):
        if self.static_routing and self.paths is not None:
            return

        if self.link_delay_estimator is None:
            self.link_delay_estimator = DefaultLinkDelayEstimator()

        self.distances = {}
        self.paths = {}
        for app in system.apps:
            delay_estimator = self.link_delay_estimator

            def app_weight_func(graph, src_node_id, dst_node_id):
                return delay_estimator(app.id, src_node_id, dst_node_id, system, environment)

            # TODO: improve this part because the shortest paths are (maybe) the same for all applications
            succ, dist = floyd_warshall.run(system, app_weight_func)
            self.distances[app.id] = dist
            self.paths[app.id] = floyd_warshall.reconstruct_all_paths(system, succ)




