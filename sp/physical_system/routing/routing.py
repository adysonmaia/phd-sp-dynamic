from abc import ABC, abstractmethod


class Routing(ABC):
    """Network Routing Abstract Class
    """

    @abstractmethod
    def get_path(self, app_id, src_node_id, dst_node_id):
        """Get path between two nodes for an application

        Args:
            app_id (int): application's id
            src_node_id (int): id of the initial node
            dst_node_id (int): id of the destination node

        Returns:
            list: list of nodes' id in the path from src_node_id to dst_node_id
        """
        return None

    @abstractmethod
    def get_path_length(self, app_id, src_node_id, dst_node_id):
        """Get distance between two nodes for an application

        Args:
            app_id (int): application's id
            src_node_id (int): id of a node
            dst_node_id (int): if of the other node

        Returns:
            float: distance between nodes. In meters if GPS coordination system is used
        """
        return None

    @abstractmethod
    def get_all_paths(self):
        """Get path between all pair of nodes for each application.
        The result is indexed by the ids of each application and node.
        E.g.:

        .. code-block:: python

            paths = routing.get_all_paths()
            app_id = 0
            src_node_id = 0
            dst_node_id = 1

            path = paths[app_id][src_node_id][dst_node_id]

        Returns:
            dict: all paths
        """
        return None

    @abstractmethod
    def get_all_paths_length(self):
        """Get distance between all pair of nodes for each application.
        The result is indexed by the ids of each application and node.
        E.g.:

        .. code-block:: python

            distances = routing.get_all_paths_length()
            app_id = 0
            src_node_id = 0
            dst_node_id = 1

            dist = distances[app_id][src_node_id][dst_node_id]

        Returns:
            dict: all distances
        """
        return None

    @abstractmethod
    def update(self, system, environment_input):
        """Update the routing based on the system's state and environment input

        Args:
            system (sp.core.model.system.System): system's state
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        """
        pass
