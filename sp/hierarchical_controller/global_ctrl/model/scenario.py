from sp.core.model.scenario import Scenario
from .network import GlobalNetwork


class GlobalScenario(Scenario):
    """Global Scenario Model Class

    Attributes:
        real_scenario (Scenario): real scenario
    """

    def __init__(self):
        """Initialization
        """
        Scenario.__init__(self)
        self.real_scenario = None

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
    def from_real_scenario(scenario, clusters):
        """Create Global Scenario from real scenario and clusters of nodes' id

        Args:
            scenario (Scenario): real scenario
            clusters (list(list)): list of clusters. Each cluster as a subsystem is a list containing nodes' id

        Returns:
            GlobalScenario: L0 scenario
        """
        return from_real_scenario(scenario, clusters)


def from_real_scenario(scenario, clusters):
    """Create Global Scenario from real scenario and clusters of nodes' id

    Args:
        scenario (Scenario): real scenario
        clusters (list(list)): list of clusters. Each cluster as a subsystem is a list containing nodes' id

    Returns:
        GlobalScenario: L0 scenario
    """
    global_scenario = GlobalScenario()
    global_scenario.real_scenario = scenario
    global_scenario.network = GlobalNetwork.from_real_network(scenario.network, clusters)

    return global_scenario
