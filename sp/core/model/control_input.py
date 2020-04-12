from sp.core.model.resource import Resource


class ControlInput:
    """Control Input Model Class
    It is used to store the control input to be applied in the system
    """
    def __init__(self):
        """Initialization
        """
        self.app_placement = {}
        self.allocated_resource = {}
        self.load_distribution = {}

    def get_app_placement(self, app_id, node_id):
        """Check if an application is placed on specific node
        Args:
            app_id (int): application's id
            node_id (int): node's id
        Returns:
            bool: True if the node hosts the application, False otherwise
        """
        return self.app_placement[app_id][node_id]

    def get_load_distribution(self, app_id, src_node_id, dst_node_id):
        """Get the load distribution of application requests from a source node to a destination node.
        The distribution is a value between 0 and 1 as the percentage of requests from the source forwarded
            to the destination node
        Args:
            app_id (int): application's id
            src_node_id (int): source node's id
            dst_node_id (int): destination node's id
        Returns:
            float: load distribution
        """
        return self.load_distribution[app_id][src_node_id][dst_node_id]

    def get_allocated_resource(self, app_id, node_id, resource_name):
        """Get the amount of allocated resource to an application on a node
        Args:
            app_id (int): application's id
            node_id (int): node's id
            resource_name (str): resource's name
        Returns:
            float: amount of allocated resource
        """
        return self.allocated_resource[app_id][node_id][resource_name]

    def get_allocated_cpu(self, app_id, node_id):
        """Get the amount of CPU allocated to an application on a node
        Args:
            app_id (int): application's id
            node_id (int): node's id
        Returns:
            float: amount of allocated resource
        """
        return self.allocated_resource[app_id][node_id][Resource.CPU]
