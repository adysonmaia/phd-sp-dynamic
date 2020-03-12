from collections import defaultdict


class System:
    def __init__(self):
        self.scenario = None
        self.environment_input = None
        self.control_input = None

        self.time = 0
        self.sampling_time = 1
        self.app_queue_size = defaultdict(lambda: defaultdict(int))
        self.processing_delay = defaultdict(lambda: defaultdict(lambda: float("inf")))

    def __copy__(self):
        cp = System()
        cp.scenario = self.scenario
        cp.environment_input = self.environment_input
        cp.control_input = self.control_input

        cp.time = self.time
        cp.sampling_time = self.sampling_time
        cp.app_queue_size = self.app_queue_size
        cp.processing_delay = self.processing_delay
        return cp

    @property
    def nodes(self):
        return self.scenario.topology.nodes

    @property
    def nodes_id(self):
        return self.scenario.topology.nodes_id

    @property
    def cloud_node(self):
        return self.scenario.topology.cloud_node

    @property
    def bs_nodes(self):
        return self.scenario.topology.bs_nodes

    @property
    def links(self):
        return self.scenario.topology.links

    @property
    def apps(self):
        return self.scenario.apps

    @property
    def apps_id(self):
        return self.scenario.apps_id

    @property
    def users(self):
        return self.scenario.users

    @property
    def users_id(self):
        return self.scenario.users_id

    @property
    def resources(self):
        return self.scenario.resources

    @property
    def resources_name(self):
        return self.scenario.resources_name

    def get_node(self, node_id):
        return self.scenario.topology.get_node(node_id)

    def get_link(self, src_node_id, dst_node_id):
        return self.scenario.topology.get_link(src_node_id, dst_node_id)

    def link_exists(self, src_node_id, dst_node_id):
        return self.scenario.topology.link_exists(src_node_id, dst_node_id)

    def get_app(self, app_id):
        return self.scenario.get_app(app_id)

    def get_user(self, user_id):
        return self.scenario.get_user(user_id)

    def get_nb_users(self, app_id=None, node_id=None):
        return self.environment_input.get_nb_users(app_id, node_id)

    def get_generated_load(self, app_id, node_id):
        return self.environment_input.get_generated_load(app_id, node_id)

    def get_net_delay(self, app_id, src_node_id, dst_node_id):
        return self.environment_input.get_net_delay(app_id, src_node_id, dst_node_id)

    def get_net_path(self, app_id, src_node_id, dst_node_id):
        return self.environment_input.get_net_path(app_id, src_node_id, dst_node_id)

    def get_processing_delay(self, app_id, node_id):
        return self.processing_delay[app_id][node_id]

    def get_app_queue_size(self, app_id, node_id):
        return self.app_queue_size[app_id][node_id]

    def get_app_placement(self, app_id, node_id):
        return self.control_input.get_app_placement(app_id, node_id)

    def get_load_distribution(self, app_id, src_node_id, dst_node_id):
        return self.control_input.get_load_distribution(app_id, src_node_id, dst_node_id)

    def get_allocated_resource(self, app_id, node_id, resource_name):
        return self.control_input.get_allocated_resource(app_id, node_id, resource_name)

    def get_allocated_cpu(self, app_id, node_id):
        return self.control_input.get_allocated_cpu(app_id, node_id)
