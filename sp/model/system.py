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
    def cloud_node(self):
        return self.scenario.topology.cloud_node

    @property
    def bs_nodes(self):
        return self.scenario.topology.bs_nodes

    @property
    def apps(self):
        return self.scenario.apps

    @property
    def users(self):
        return self.scenario.users

    @property
    def resources(self):
        return self.scenario.resources

