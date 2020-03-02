from sp.core.estimator import Estimator
from sp.core.model import Resource
from abc import abstractmethod


INF = float("inf")


class AppQueueSizeEstimator(Estimator):
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


class DefaultAppQueueSizeEstimator(AppQueueSizeEstimator):
    def calc(self, system, app_id, node_id):
        return 0.0


class MM1AppQueueSizeEstimator(AppQueueSizeEstimator):
    def calc(self, system, app_id, node_id):
        if system.control is None:
            return 0.0
        else:
            app = system.get_app(app_id)
            dst_node = system.get_node(node_id)
            alloc_cpu = system.get_allocated_resource(app.id, dst_node.id, Resource.CPU)

            service_rate = 0.0
            if app.work_size > 0.0:
                service_rate = alloc_cpu / float(app.work_size)

            arrival_rate = 0.0
            for src_node in system.nodes:
                ld = system.get_load_distribution(app.id, src_node.id, dst_node.id)
                gen_load = system.get_generated_load(app.id, src_node.id)
                arrival_rate += gen_load * ld

            if service_rate > arrival_rate:
                p = arrival_rate / service_rate
                # return p / float(1.0 - p)
                return (p ** 2) / float(1.0 - p)
            else:
                # TODO: what to do in this case?
                return INF
