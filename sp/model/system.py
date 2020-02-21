class System:
    def __init__(self):
        self.time = 0
        self.scenario = None
        self.app_placement = {}
        self.app_queue_size = {}
        self.app_resource_alloc = {}
        self.load_distribution = {}
        self.request_load = {}
        self.net_delay = {}
        self.net_path = {}

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
        return self.topology.get_node(node_id)

    def get_link(self, src_node_id, dst_node_id):
        return self.topology.get_link(src_node_id, dst_node_id)

    def link_exists(self, src_node_id, dst_node_id):
        return self.topology.link_exists(src_node_id, dst_node_id)

    def get_app(self, app_id):
        return self.scenario.get_app(app_id)

    def get_user(self, user_id):
        return self.scenario.get_user(user_id)

