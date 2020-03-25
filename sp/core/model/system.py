from collections import defaultdict
import math

ERROR_TOLERANCE = 0.01


class System:
    def __init__(self):
        self.scenario = None
        self.environment_input = None
        self.control_input = None

        self.time = 0
        self.sampling_time = 1
        self.app_queue_size = defaultdict(lambda: defaultdict(int))
        self.processing_delay = defaultdict(lambda: defaultdict(lambda: math.inf))

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

    def __eq__(self, other):
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
        return self.scenario.network.nodes

    @property
    def nodes_id(self):
        return self.scenario.network.nodes_id

    @property
    def cloud_node(self):
        return self.scenario.network.cloud_node

    @property
    def bs_nodes(self):
        return self.scenario.network.bs_nodes

    @property
    def links(self):
        return self.scenario.network.links

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
        return self.scenario.network.get_node(node_id)

    def get_link(self, src_node_id, dst_node_id):
        return self.scenario.network.get_link(src_node_id, dst_node_id)

    def link_exists(self, src_node_id, dst_node_id):
        return self.scenario.network.link_exists(src_node_id, dst_node_id)

    def get_app(self, app_id):
        return self.scenario.get_app(app_id)

    def get_user(self, user_id):
        return self.scenario.get_user(user_id)

    def get_processing_delay(self, app_id, node_id):
        return self.processing_delay[app_id][node_id]

    def get_app_queue_size(self, app_id, node_id):
        return self.app_queue_size[app_id][node_id]
