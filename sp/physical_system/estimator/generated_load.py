from sp.core.estimator import Estimator
from abc import abstractmethod


class GeneratedLoadEstimator(Estimator):
    def calc_app_loads(self, app_id, system, environment_input):
        app = system.get_app(app_id)
        loads = {}
        for node in system.nodes:
            loads[node.id] = self.calc(app.id, node.id, system, environment_input)
        return loads

    def calc_node_loads(self, node_id, system, environment_input):
        node = system.get_node(node_id)
        loads = {}
        for app in system.apps:
            loads[app.id] = self.calc(app.id, node.id, system, environment_input)
        return loads

    def calc_all_loads(self, system, environment_input):
        loads = {}
        for app in system.apps:
            loads[app.id] = self.calc_app_loads(app.id, system, environment_input)
        return loads

    @abstractmethod
    def calc(self, app_id, node_id, system, environment_input):
        pass


class DefaultGeneratedLoadEstimator(GeneratedLoadEstimator):
    def calc(self, app_id, node_id, system, environment_input):
        nb_users = environment_input.get_nb_users(app_id, node_id)
        app = system.get_app(app_id)
        return float(app.request_rate * nb_users)
