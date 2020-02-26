from . import Estimator
from abc import abstractmethod


class QueueSizeEstimator(Estimator):
    def calc_app_queue_sizes(self, system, app_id):
        app = system.get_app(app_id)
        q_sizes = {}
        for node in system.nodes:
            q_sizes[node.id] = self.calc(system, app.id, node.id)
        return q_sizes

    def calc_node_queue_sizes(self, system, node_id):
        node = system.get_node(node_id)
        q_sizes = {}
        for app in system.apps:
            q_sizes[app.id] = self.calc(system, app.id, node.id)
        return q_sizes

    def calc_all_queue_sizes(self, system):
        loads = {}
        for app in system.apps:
            loads[app.id] = self.calc_app_queue_sizes(system, app.id)
        return loads

    @abstractmethod
    def calc(self, system, app_id, node_id):
        pass


class DefaultQueueSizeEstimator(QueueSizeEstimator):
    def calc(self, system, app_id, node_id):
        return 0.0
