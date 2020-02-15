class State:
    def __init__(self):
        self.time = -1
        self.environment_input = Environment()
        self.control_decision = Control()
        self.app_queue_size = {}
        self.response_time = {}

    def get_net_delay(self, app_id, src_node_id, dst_node_id):
        return self.environment_input.get_net_delay(app_id, src_node_id, dst_node_id)

    def set_net_delay(self, app_id, src_node_id, dst_node_id, value):
        self.environment_input.set_net_delay(app_id, src_node_id, dst_node_id, value)

    def get_req_load(self, app_id, node_id):
        return self.environment_input.get_req_load(app_id, node_id)

    def set_req_load(self, app_id, node_id, value):
        return self.environment_input.set_req_load(app_id, node_id, value)

    def is_placed(self, app_id, node_id):
        return self.control_decision.get_placement(app_id, node_id)

    def set_place(self, app_id, node_id, value):
        self.control_decision.get_placement(app_id, node_id, value)

    def get_load_dist(self, app_id, src_node_id, dst_node_id):
        return self.control_decision.get_distribution(app_id, src_node_id, dst_node_id)

    def get_app_queue_size(self, app_id, node_id):
        return self.app_queue_size[app_id, node_id]

    def set_app_queue_size(self, app_id, node_id, value):
        self.app_queue_size[app_id, node_id] = value

    def get_response_time(self, app_id, src_node_id, dst_node_id):
        return self.response_time[app_id, src_node_id, dst_node_id]

    def set_response_time(self, app_id, src_node_id, dst_node_id, value):
        self.response_time[app_id, src_node_id, dst_node_id] = value


class Environment:
    def __init__(self):
        self.net_delay = {}
        self.request_load = {}

    def get_net_delay(self, app_id, src_node_id, dst_node_id):
        key_1 = (app_id, src_node_id, dst_node_id)
        key_2 = (app_id, dst_node_id, src_node_id)
        if key_1 in self.net_delay:
            return self.net_delay[key_1]
        elif key_2 in self.net_delay:
            return self.net_delay[key_2]
        else:
            raise KeyError("Key (%s) not found" % key_1)

    def set_net_delay(self, app_id, src_node_id, dst_node_id, value):
        self.net_delay[app_id, src_node_id, dst_node_id] = value
        self.net_delay[app_id, dst_node_id, src_node_id] = value

    def get_req_load(self, app_id, node_id):
        return self.request_load[app_id, node_id]

    def set_req_load(self, app_id, node_id, value):
        self.request_load[app_id, node_id] = value


class Control:
    def __init__(self):
        self.placement = {}
        self.distribution = {}

    def get_placement(self, app_id, node_id):
        return self.placement[app_id, node_id]

    def set_placement(self, app_id, node_id, value):
        self.placement[app_id, node_id] = value

    def get_distribution(self, app_id, src_node_id, dst_node_id):
        return self.distribution[app_id, src_node_id, dst_node_id]

    def set_distribution(self, app_id, src_node_id, dst_node_id, value):
        self.distribution[app_id, src_node_id, dst_node_id] = value
