class EnvironmentInput:
    def __init__(self):
        self.generated_load = {}
        self.net_delay = {}
        self.net_path = {}
        self.attached_users = {}

    def __copy__(self):
        cp = EnvironmentInput()
        cp.generated_load = self.generated_load
        cp.net_delay = self.net_delay
        cp.net_path = self.net_path
        cp.attached_users = self.attached_users
        return cp

    def get_generated_load(self, app_id, node_id):
        return self.generated_load[app_id][node_id]

    def get_net_delay(self, app_id, src_node_id, dst_node_id):
        return self.net_delay[app_id][src_node_id][dst_node_id]

    def get_net_path(self, app_id, src_node_id, dst_node_id):
        return self.net_path[app_id][src_node_id][dst_node_id]

    def get_attached_users(self):
        return self.attached_users.values()

    def get_nb_users(self, app_id=None, node_id=None):
        count = 0
        for user in self.get_attached_users():
            if (app_id is None or user.app_id == app_id) and (node_id is None or user.node_id == node_id):
                count += 1
        return count

    @staticmethod
    def create_empty(system):
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
                    env.net_delay[app.id][node.id][dst_node.id] = float("inf")
                    env.net_path[app.id][node.id][dst_node.id] = None

        return env



