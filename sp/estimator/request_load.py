from . import Estimator


class RequestLoadEstimator(Estimator):
    def __init__(self, system=None):
        self.system = system

    def calc_app_loads(self, app_id):
        app = self.system.get_app(app_id)
        loads = {}
        for node in self.system.nodes:
            loads[node.id] = self.calc(app.id, node.id)
        return loads

    def calc_node_loads(self, node_id):
        node = self.system.get_node(node_id)
        loads = {}
        for app in self.system.apps:
            loads[app.id] = self.calc(app.id, node.id)
        return loads

    def calc_all_loads(self):
        loads = {}
        for app in self.system.apps:
            loads[app.id] = self.calc_app_loads(app.id)

    def calc(self, app_id, node_id):
        return None


class DefaultRequestLoadEstimator(RequestLoadEstimator):
    def __init__(self, system=None):
        RequestLoadEstimator.__init__(self, system)

    def calc(self, app_id, node_id):
        nb_users = self.system.get_nb_users(app_id, node_id)
        app = self.system.get_app(app_id)
        return float(app.request_rate * nb_users)
