import math


class EnvironmentInput:
    """Environment Input Model Class

    It is used to store information about the environment.
    That is, system's parameters that are not directly controlled by the system controller
    """
    def __init__(self):
        self.generated_load = {}
        self.net_delay = {}
        self.net_path = {}
        self.attached_users = {}

    def __copy__(self):
        """Shallow copy

        Returns:
            EnvironmentInput: the shallow copy
        """
        cp = EnvironmentInput()
        cp.generated_load = self.generated_load
        cp.net_delay = self.net_delay
        cp.net_path = self.net_path
        cp.attached_users = self.attached_users
        return cp

    def get_generated_load(self, app_id, node_id):
        """Get the amount of application requests generated from users attached to a node

        Args:
            app_id (int): application's id. Get the load from a specified application
            node_id (int): node's id
        Returns:
            float: generated load
        """
        return self.generated_load[app_id][node_id]

    def get_net_delay(self, app_id, src_node_id, dst_node_id):
        """Get the network delay to transmit one request of an application from a source node to a destination node

        Args:
            app_id (int): application's id
            src_node_id (int): source node's id
            dst_node_id (int): destination node's id
        Returns:
            float: network delay
        """
        return self.net_delay[app_id][src_node_id][dst_node_id]

    def get_net_path(self, app_id, src_node_id, dst_node_id):
        """Get a network path from a source node to a destination node for a specific application

        Args:
            app_id (int): application's id
            src_node_id (int): source node's id
            dst_node_id (int): destination node's id
        Returns:
            list(int): list of node's id in the path from source to destination node
        """
        return self.net_path[app_id][src_node_id][dst_node_id]

    def get_attached_users(self):
        """Get all users after the attachment procedure

        Returns:
            list(sp.core.model.user.User): list of users
        """
        return self.attached_users.values()

    def get_nb_users(self, app_id=None, node_id=None):
        """Get the number of users from an application and/or attached to a node

        Args:
            app_id (int, optional): application's id. If specified, it only counts users from the specified application
            node_id (int, optional): node's id. If specified, it only counts users attached to the specified node
        Returns:
            int: number of users
        """
        count = 0
        for user in self.get_attached_users():
            app_selected = app_id is None or user.app_id == app_id
            node_selected = node_id is None or (hasattr(user, 'node_id') and user.node_id == node_id)
            if app_selected and node_selected:
                count += 1
        return count

    @staticmethod
    def create_empty(system):
        """Create an empty environment input based on a system's state

        Args:
            system (sp.core.model.system.System): system's state
        Returns:
            EnvironmentInput: an empty environment input
        """
        env = EnvironmentInput()

        for app in system.apps:
            env.generated_load[app.id] = {}
            env.net_delay[app.id] = {}
            env.net_path[app.id] = {}

            for node in system.nodes:
                env.generated_load[app.id][node.id] = 0.0
                env.net_delay[app.id][node.id] = {}
                env.net_path[app.id][node.id] = {}

                for dst_node in system.nodes:
                    env.net_delay[app.id][node.id][dst_node.id] = math.inf
                    env.net_path[app.id][node.id][dst_node.id] = None

        return env



