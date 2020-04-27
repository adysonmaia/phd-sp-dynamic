from sp.core.estimator import Estimator
from abc import abstractmethod


class GeneratedLoadEstimator(Estimator):
    def calc_app_loads(self, app_id, system, environment_input, **kwargs):
        app = system.get_app(app_id)
        loads = {}
        for node in system.nodes:
            loads[node.id] = self.calc(app.id, node.id, system, environment_input, **kwargs)
        return loads

    def calc_node_loads(self, node_id, system, environment_input, **kwargs):
        node = system.get_node(node_id)
        loads = {}
        for app in system.apps:
            loads[app.id] = self.calc(app.id, node.id, system, environment_input, **kwargs)
        return loads

    def calc_all_loads(self, system, environment_input, **kwargs):
        loads = {}
        for app in system.apps:
            loads[app.id] = self.calc_app_loads(app.id, system, environment_input, **kwargs)
        return loads

    @abstractmethod
    def calc(self, app_id, node_id, system, environment_input, **kwargs):
        pass


class DefaultGeneratedLoadEstimator(GeneratedLoadEstimator):
    def calc(self, app_id, node_id, system, environment_input, time_tolerance=None):
        nb_users = environment_input.get_nb_users(app_id, node_id)
        app = system.get_app(app_id)
        users_load = float(app.request_rate * nb_users)

        load_estimator = system.get_load_estimator(app_id, node_id)
        extra_load = 0.0
        if load_estimator is not None:
            extra_load = load_estimator(system.time, time_tolerance=time_tolerance)

        return users_load + extra_load
