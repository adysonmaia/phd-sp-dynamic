from .import Estimator

INF = float("inf")


class LinkDelayEstimator(Estimator):
    def __init__(self, system=None):
        Estimator.__init__(self)
        self.system = system

    def calc(self, app_id, src_node_id, dst_node_id):
        return INF


class DefaultLinkDelayEstimator(LinkDelayEstimator):
    def __init__(self, system=None):
        LinkDelayEstimator.__init__(self, system)

    def calc(self, app_id, src_node_id, dst_node_id):
        if self.system.link_exists(src_node_id, dst_node_id):
            app = self.system.get_app(app_id)
            link = self.system.get_link(src_node_id, dst_node_id)

            return link.propagation_delay + app.data_size / float(link.bandwidth)
        else:
            return INF
