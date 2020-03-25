from sp.core.estimator import Estimator
from abc import abstractmethod
import math


class LinkDelayEstimator(Estimator):
    @abstractmethod
    def calc(self, app_id, src_node_id, dst_node_id, system, environment_input):
        pass


class DefaultLinkDelayEstimator(LinkDelayEstimator):
    def calc(self, app_id, src_node_id, dst_node_id, system, environment_input):
        if system.link_exists(src_node_id, dst_node_id):
            app = system.get_app(app_id)
            link = system.get_link(src_node_id, dst_node_id)

            return link.propagation_delay + app.data_size / float(link.bandwidth)
        else:
            return math.inf
