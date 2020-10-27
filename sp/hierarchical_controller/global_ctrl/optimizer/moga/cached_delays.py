from sp.system_controller.optimizer.soga.cached_delays import CachedDelays


class GlobalCachedDelays(CachedDelays):

    def __init__(self):
        """Initialization
        """
        CachedDelays.__init__(self)

    def invalidate(self, app_id, src_node_id, dst_node_id):
        """Invalidate a cached delay

        Args:
            app_id (int): application's id
            src_node_id (int): source node's id
            dst_node_id (int): destination node's id
        """
        self._proc_delay[app_id][dst_node_id] = None
        self._net_delay[app_id][dst_node_id][dst_node_id] = None
