from . import Estimator
from abc import abstractmethod


class RequestLoadEstimator(Estimator):
    def calc_app_loads(self, system, app_id):
        app = system.get_app(app_id)
        loads = {}
        for node in system.nodes:
            loads[node.id] = self.calc(system, app.id, node.id)
        return loads

    def calc_node_loads(self, system, node_id):
        node = system.get_node(node_id)
        loads = {}
        for app in system.apps:
            loads[app.id] = self.calc(system, app.id, node.id)
        return loads

    def calc_all_loads(self, system):
        loads = {}
        for app in system.apps:
            loads[app.id] = self.calc_app_loads(system, app.id)
        return loads

    @abstractmethod
    def calc(self, system, app_id, node_id):
        pass


class DefaultRequestLoadEstimator(RequestLoadEstimator):
    def calc(self, system, app_id, node_id):
        nb_users = system.get_nb_users(app_id, node_id)
        app = system.get_app(app_id)
        return float(app.request_rate * nb_users)
