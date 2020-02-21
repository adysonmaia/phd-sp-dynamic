from . import Estimator


class QueueSizeEstimator(Estimator):
    def __init__(self, system=None):
        self.system = system

    def calc_app_queue_sizes(self, app_id):
        app = self.system.get_app(app_id)
        q_sizes = {}
        for node in self.system.nodes:
            q_sizes[node.id] = self.calc(app.id, node.id)
        return q_sizes

    def calc_node_queue_sizes(self, node_id):
        node = self.system.get_node(node_id)
        q_sizes = {}
        for app in self.system.apps:
            q_sizes[app.id] = self.calc(app.id, node.id)
        return q_sizes

    def calc_all_queue_sizes(self):
        loads = {}
        for app in self.system.apps:
            loads[app.id] = self.calc_app_queue_sizes(app.id)

    def calc(self, app_id, node_id):
        return None


class DefaultQueueSizeEstimator(QueueSizeEstimator):
    def __init__(self, system=None):
        QueueSizeEstimator.__init__(self, system)

    def calc(self, app_id, node_id):
        return 0.0