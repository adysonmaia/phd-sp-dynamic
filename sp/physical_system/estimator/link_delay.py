from sp.core.estimator import Estimator
from abc import abstractmethod
import math


class LinkDelayEstimator(Estimator):
    """Link Delay Estimator Abstract Class
    """

    @abstractmethod
    def calc(self, app_id, src_node_id, dst_node_id, system, environment_input):
        """Estimate network delay in a link between two nodes for an application

        Args:
            app_id (int): application's id
            src_node_id (int): id of a node
            dst_node_id (int): if of the other node
            system (sp.core.model.system.System): system
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input

        Returns:
            float: delay
        """
        pass


class DefaultLinkDelayEstimator(LinkDelayEstimator):
    """Default Link Delay Estimator

    It estimates the network transmission delay of application request in a link
    """

    def calc(self, app_id, src_node_id, dst_node_id, system, environment_input):
        """Estimate network delay in a link between two nodes for an application

        Args:
            app_id (int): application's id
            src_node_id (int): id of a node
            dst_node_id (int): if of the other node
            system (sp.core.model.system.System): system
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input

        Returns:
            float: delay
        """
        if system.link_exists(src_node_id, dst_node_id):
            app = system.get_app(app_id)
            link = system.get_link(src_node_id, dst_node_id)

            return link.propagation_delay + app.data_size / float(link.bandwidth)
        else:
            return math.inf
