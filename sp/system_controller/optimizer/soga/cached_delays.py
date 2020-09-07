from collections import defaultdict
import math


class CachedDelays:
    """Cached Delays
    """

    def __init__(self):
        """Initialization
        """
        self._net_delay = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None)))
        self._proc_delay = defaultdict(lambda: defaultdict(lambda: None))
        self._init_delay = defaultdict(lambda: defaultdict(lambda: None))

    def is_valid(self, app_id, src_node_id, dst_node_id):
        """Check if a cached response time is valid

        Args:
            app_id (int): application's id
            src_node_id (int): source node's id
            dst_node_id (int): destination node's id
        Returns:
            bool: valid or not
        """
        return (self.is_net_delay_valid(app_id, src_node_id, dst_node_id)
                and self.is_proc_delay_valid(app_id, dst_node_id)
                and self.is_init_delay_valid(app_id, dst_node_id))

    def is_net_delay_valid(self, app_id, src_node_id, dst_node_id):
        """Check if a cached network delay if valid

        Args:
            app_id (int): application's id
            src_node_id (int): source node's id
            dst_node_id (int): destination node's id
        Returns:
            bool: valid or not
        """
        return self._net_delay[app_id][src_node_id][dst_node_id] is not None

    def is_proc_delay_valid(self, app_id, node_id):
        """Check if a cached processing delay is valid

        Args:
            app_id (int): application's id
            node_id (int): node's id
        Returns:
            bool: valid or not
        """
        return self._proc_delay[app_id][node_id] is not None

    def is_init_delay_valid(self, app_id, node_id):
        """Check if a cached initialization delay is valid

        Args:
            app_id (int): application's id
            node_id (int): node's id
        Returns:
            bool: valid or not
        """
        return self._init_delay[app_id][node_id] is not None

    def get_net_delay(self, app_id, src_node_id, dst_node_id):
        """Get a cached network delay

        Args:
            app_id (int): application's id
            src_node_id (int): source node's id
            dst_node_id (int): destination node's id
        Returns:
            float: delay value
        """
        delay = self._net_delay[app_id][src_node_id][dst_node_id]
        return delay if delay is not None else math.inf

    def get_proc_delay(self, app_id, node_id):
        """Get a cached processing delay

        Args:
            app_id (int): application's id
            node_id (int): node's id
        Returns:
            float: delay value
        """
        delay = self._proc_delay[app_id][node_id]
        return delay if delay is not None else math.inf

    def get_init_delay(self, app_id, node_id):
        """Get a cached initialization delay

        Args:
            app_id (int): application's id
            node_id (int): node's id
        Returns:
            float: delay value
        """
        delay = self._init_delay[app_id][node_id]
        return delay if delay is not None else math.inf

    def get_rt(self, app_id, src_node_id, dst_node_id):
        """Get a cached response time

        Args:
            app_id (int): application's id
            src_node_id (int): source node's id
            dst_node_id (int): destination node's id
        Returns:
            float: delay value
        """
        return (self.get_net_delay(app_id, src_node_id, dst_node_id)
                + self.get_proc_delay(app_id, dst_node_id)
                + self.get_init_delay(app_id, dst_node_id))

    def set_net_delay(self, app_id, src_node_id, dst_node_id, value):
        """Set a network delay

        Args:
            app_id (int): application's id
            src_node_id (int): source node's id
            dst_node_id (int): destination node's id
            value (float): delay value
        """
        self._net_delay[app_id][src_node_id][dst_node_id] = value

    def set_proc_delay(self, app_id, node_id, value):
        """Set a processing delay

        Args:
            app_id (int): application's id
            node_id (int): node's id
            value (float): delay value
        """
        self._proc_delay[app_id][node_id] = value

    def set_init_delay(self, app_id, node_id, value):
        """Set an initialization delay

        Args:
            app_id (int): application's id
            node_id (int): node's id
            value (float): delay value
        """
        self._init_delay[app_id][node_id] = value

    def invalidate(self, app_id, src_node_id, dst_node_id):
        """Invalidate a cached delay

        Args:
            app_id (int): application's id
            src_node_id (int): source node's id
            dst_node_id (int): destination node's id
        """
        self._proc_delay[app_id][dst_node_id] = None