from collections import defaultdict
import math

ERROR_TOLERANCE = 0.01


class System:
    """System Model Class
    It is used to store the state of the system in a particular time

    Attributes:
        scenario (sp.core.model.Scenario): system's scenario
        environment_input (sp.core.model.EnvironmentInput): environment input that created system's state
        control_input (sp.core.model.ControlInput): control input that created system's state
        time (float): time where the system's state started
        sampling_time (float): the duration of the system's state
    """
    def __init__(self):
        self.scenario = None
        self.environment_input = None
        self.control_input = None

        self.time = 0
        self.sampling_time = 1
        self.app_queue_size = defaultdict(lambda: defaultdict(int))
        self.processing_delay = defaultdict(lambda: defaultdict(lambda: math.inf))

    def __copy__(self):
        """Shallow copy
        Returns:
            System: the shallow copy
        """
        cp = System()
        cp.scenario = self.scenario
        cp.environment_input = self.environment_input
        cp.control_input = self.control_input

        cp.time = self.time
        cp.sampling_time = self.sampling_time
        cp.app_queue_size = self.app_queue_size
        cp.processing_delay = self.processing_delay
        return cp

    def clear_copy(self):
        """Copy system's state with its (control and environment) inputs undefined
        Returns:
            System: an empty system's state
        """
        new_system = System()
        new_system.scenario = self.scenario
        new_system.time = self.time
        new_system.sampling_time = self.sampling_time
        return new_system

    def __eq__(self, other):
        """Compare if two system's state are equals
        Args:
            other (System): other state
        Returns:
            bool: whether two system's state are equals or not
        """
        if self.time != other.time or self.sampling_time != other.sampling_time:
            return False

        for app in self.apps:
            for node in self.nodes:
                queue_size_1 = self.get_app_queue_size(app.id, node.id)
                queue_size_2 = other.get_app_queue_size(app.id, node.id)

                if math.isinf(queue_size_1) and not math.isinf(queue_size_2):
                    return False
                elif not math.isinf(queue_size_1) and math.isinf(queue_size_2):
                    return False
                elif abs(queue_size_1 - queue_size_2) > ERROR_TOLERANCE:
                    return False

                proc_1 = self.get_processing_delay(app.id, node.id)
                proc_2 = other.get_processing_delay(app.id, node.id)

                if math.isinf(proc_1) and not math.isinf(proc_2):
                    return False
                elif not math.isinf(proc_1) and math.isinf(proc_2):
                    return False
                elif abs(proc_1 - proc_2) > ERROR_TOLERANCE:
                    return False

        return True

    @property
    def nodes(self):
        """Get all nodes of the system's scenario
        Returns:
            list(sp.core.model.Node): list of nodes
        """
        return self.scenario.network.nodes

    @property
    def nodes_id(self):
        """Get the ids from all nodes of the system's scenario
        Returns:
            list(int): list of nodes' id
        """
        return self.scenario.network.nodes_id

    @property
    def cloud_node(self):
        """Get the cloud node
        Returns:
            sp.core.model.Node: cloud node
        """
        return self.scenario.network.cloud_node

    @property
    def bs_nodes(self):
        """Get all base station (edge) nodes of the system's scenario
        Returns:
            list(sp.core.model.Node): list of nodes
        """
        return self.scenario.network.bs_nodes

    @property
    def links(self):
        """Get all network links of the system's scenario
        Returns:
            list(sp.core.model.Link): list of links
        """
        return self.scenario.network.links

    @property
    def apps(self):
        """Get all applications of the system's scenario
        Returns:
            list(sp.core.model.Application): list of applications
        """
        return self.scenario.apps

    @property
    def apps_id(self):
        """Get the ids from all applications of the system's scenario
        Returns:
            list(int): list of applications' id
        """
        return self.scenario.apps_id

    @property
    def users(self):
        """Get all users of the system's scenario
        Returns:
            list(sp.core.model.User): list of users
        """
        return self.scenario.users

    @property
    def users_id(self):
        """Get the ids from all users of the system's scenario
        Returns:
            list(int): list of users' id
        """
        return self.scenario.users_id

    @property
    def resources(self):
        """Get all resources' type of the system's scenario
        Returns:
            list(sp.core.model.Resource): list of resources
        """
        return self.scenario.resources

    @property
    def resources_name(self):
        """Get the names from all resources of the system's scenario
        Returns:
            list(str): list of resources' name
        """
        return self.scenario.resources_name

    def get_node(self, node_id):
        """Get a node by its id
        Args:
            node_id (int): node's id
        Returns:
            sp.core.model.Node: node
        Raises:
            KeyError: node not found with the specified id
        """
        return self.scenario.network.get_node(node_id)

    def get_link(self, src_node_id, dst_node_id):
        """Get the network link between two nodes
        Args:
            src_node_id (int): node's id
            dst_node_id (int): other node's id
        Returns:
            sp.core.model.Link: network link
        Raises:
            KeyError: link not found between the nodes
        """
        return self.scenario.network.get_link(src_node_id, dst_node_id)

    def link_exists(self, src_node_id, dst_node_id):
        """Check if exists a network link between two nodes
        Args:
            src_node_id (int): node's id
            dst_node_id (int): other node's id
        Returns:
            bool: whether link exists or not
        """
        return self.scenario.network.link_exists(src_node_id, dst_node_id)

    def get_app(self, app_id):
        """Get an application by its id
        Args:
            app_id (int): application's id
        Returns:
            sp.core.model.Application: application
        Raises:
            KeyError: no application found for the specified id
        """
        return self.scenario.get_app(app_id)

    def get_user(self, user_id):
        """Get a user by its id
        Args:
            user_id (int): user's id
        Returns:
            sp.core.model.User: user
        Raises:
            KeyError: no user found for the specified id
        """
        return self.scenario.get_user(user_id)

    def get_load_estimator(self, app_id, node_id):
        return self.scenario.get_load_estimator(app_id, node_id)

    def get_processing_delay(self, app_id, node_id):
        """Get the application's processing delay on a node according to system's state
        Args:
            app_id (int): application's id
            node_id (int): node's id
        Returns:
            float: processing delay
        """
        return self.processing_delay[app_id][node_id]

    def get_app_queue_size(self, app_id, node_id):
        """Get the size of application's queue on a node according to system's state
        Args:
            app_id (int): application's id
            node_id (int): node's id
        Returns:
            float: queue's size
        """
        return self.app_queue_size[app_id][node_id]
