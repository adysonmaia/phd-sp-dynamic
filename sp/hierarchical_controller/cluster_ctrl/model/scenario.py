from sp.core.model import Scenario
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalNode
from .network import ClusterNetwork


class ClusterScenario(Scenario):
    """Cluster Scenario

    Attributes:
        real_scenario (Scenario): real scenario
        id (int): cluster's id
    """

    def __init__(self):
        """Initialization

        """
        Scenario.__init__(self)
        self.real_scenario = None
        self.id = None

    @property
    def _apps(self):
        return self.real_scenario._apps

    @_apps.setter
    def _apps(self, value):
        pass

    @property
    def _users(self):
        return self.real_scenario._users

    @_users.setter
    def _users(self, value):
        pass

    @property
    def _resources(self):
        return self.real_scenario._resources

    @_resources.setter
    def _resources(self, value):
        pass

    @staticmethod
    def from_global_scenario(global_scenario, global_node):
        """Create cluster scenario from global scenario

        Args:
            global_scenario (GlobalScenario): global scenario
            global_node (GlobalNode): global node

        Returns:
            ClusterScenario: cluster scenario
        """
        return from_global_scenario(global_scenario, global_node)


def from_global_scenario(global_scenario, global_node):
    """Create cluster scenario from global scenario

    Args:
        global_scenario (GlobalScenario): global scenario
        global_node (GlobalNode): global node

    Returns:
        ClusterScenario: cluster scenario
    """

    cluster_scenario = ClusterScenario()
    cluster_scenario.id = global_node.id
    cluster_scenario.real_scenario = global_scenario.real_scenario
    cluster_scenario.network = ClusterNetwork.from_global_network(global_scenario.network, global_node)

    return cluster_scenario





