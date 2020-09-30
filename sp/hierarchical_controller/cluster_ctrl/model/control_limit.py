from collections import defaultdict


class ClusterControlLimit:
    """Cluster Control Limit

    """

    def __init__(self):
        """Initialization

        """
        self.max_dispatch_load = defaultdict(lambda: defaultdict(float))
        self.max_app_placement = defaultdict(int)
        self.min_app_placement = defaultdict(int)

    def get_max_dispatch_load(self, app_id, node_id):
        """Get max load that can be dispatched to a node

        Args:
            app_id (int): application's id
            node_id (int): node's id

        Returns:
            float: load
        """
        return self.max_dispatch_load[app_id][node_id]

    def get_max_app_placement(self, app_id):
        """Get max number of instances for an application

        Args:
            app_id (int): application's id

        Returns:
            int: number of instances
        """
        return self.max_app_placement[app_id]

    def get_min_app_placement(self, app_id):
        """Get min number of instances for an application

        Args:
            app_id (int): application's id

        Returns:
            int: number of instances
        """
        return self.min_app_placement[app_id]
