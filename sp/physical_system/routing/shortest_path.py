from .routing import Routing
from sp.physical_system.estimator import LinkDelayEstimator, DefaultLinkDelayEstimator
from sp.physical_system.util import floyd_warshall


class ShortestPathRouting(Routing):
    """Network Routing using Shortest Path

    Attributes:
        static_routing (bool): whether routing is static over time or not. It is True by default
        link_delay_estimator (LinkDelayEstimator): link delay estimator
        paths (dict): all network paths for each application
        distances (dict): all network distances for each application
    """

    def __init__(self):
        """Initialization
        """
        Routing.__init__(self)
        self.static_routing = True
        self.link_delay_estimator = None

        self.paths = None
        self.distances = None

    def get_path(self, app_id, src_node_id, dst_node_id):
        """Get path between two nodes for an application

        Args:
            app_id (int): application's id
            src_node_id (int): id of the initial node
            dst_node_id (int): id of the destination node

        Returns:
            list: list of nodes' id in the path
        """

        return self.paths[app_id][src_node_id][dst_node_id]

    def get_path_length(self, app_id, src_node_id, dst_node_id):
        """Get distance between two nodes for an application

        Args:
            app_id (int): application's id
            src_node_id (int): id of a node
            dst_node_id (int): id of the other node

        Returns:
            float: distance
        """
        return self.distances[app_id][src_node_id][dst_node_id]

    def get_all_paths(self):
        """Get path between all pair of nodes for each application

        Returns:
            dict: all paths
        """
        return self.paths

    def get_all_paths_length(self):
        """Get distance between all pair of nodes for each application

        Returns:
            dict: all distances
        """
        return self.distances

    def update(self, system, environment_input):
        """Update the routing based on the system's state and environment input

        Args:
            system (sp.core.model.system.System): system's state
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        """

        if self.static_routing and self.paths is not None:
            return

        if self.link_delay_estimator is None:
            self.link_delay_estimator = DefaultLinkDelayEstimator()

        self.distances = {}
        self.paths = {}
        for app in system.apps:
            delay_estimator = self.link_delay_estimator

            def app_weight_func(graph, src_node_id, dst_node_id):
                return delay_estimator(app.id, src_node_id, dst_node_id, system, environment_input)

            # TODO: improve this part because the shortest paths are (maybe) the same for all applications
            succ, dist = floyd_warshall.run(system, app_weight_func)
            self.distances[app.id] = dist
            self.paths[app.id] = floyd_warshall.reconstruct_all_paths(system, succ)




