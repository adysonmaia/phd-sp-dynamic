from .import Estimator
from abc import abstractmethod

INF = float("inf")


class LinkDelayEstimator(Estimator):
    @abstractmethod
    def calc(self, system, app_id, src_node_id, dst_node_id):
        pass


class DefaultLinkDelayEstimator(LinkDelayEstimator):
    def calc(self, system, app_id, src_node_id, dst_node_id):
        if system.link_exists(src_node_id, dst_node_id):
            app = system.get_app(app_id)
            link = system.get_link(src_node_id, dst_node_id)

            return link.propagation_delay + app.data_size / float(link.bandwidth)
        else:
            return INF
