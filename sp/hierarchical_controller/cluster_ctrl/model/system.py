from sp.core.model import System, Scenario, Node
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalNode
from .scenario import ClusterScenario
from .control_input import ClusterControlInput
from .environment_input import ClusterEnvironmentInput


class ClusterSystem(System):
    """Cluster System Model Class

    Attributes:
        real_scenario (Scenario): real scenario
    """

    def __init__(self):
        """Initialization
        """
        System.__init__(self)
        self.real_scenario = None

    def __copy__(self):
        """Shallow copy

        Returns:
            GlobalSystem: the shallow copy
        """
        cp = System.__copy__(self)
        cp.real_scenario = self.real_scenario
        return cp

    def clear_copy(self):
        """Copy system's state with its (control and environment) inputs undefined

        Returns:
            GlobalSystem: an empty system's state
        """
        cp = System.clear_copy(self)
        cp.real_scenario = self.real_scenario
        return cp

    @property
    def id(self):
        return self.scenario.id

    @property
    def internal_nodes(self):
        """Get nodes inside the cluster

        Returns:
            list(Node): real nodes
        """
        return self.scenario.network.internal_nodes

    @property
    def external_nodes(self):
        """Get external cluster nodes

        Returns:
            list(GlobalNode): external nodes as clusters
        """
        return self.scenario.network.external_nodes

    @staticmethod
    def from_real_system(system, global_scenario, global_node):
        """Create cluster system from real system's state

        Args:
            system (System): real system
            global_scenario (GlobalScenario): global scenario
            global_node (GlobalNode): global node representing the cluster

        Returns:
            ClusterSystem: cluster system
        """
        return from_real_system(system, global_scenario, global_node)


def from_real_system(system, global_scenario, global_node):
    """Create cluster system from real system's state

    Args:
        system (System): real system
        global_scenario (GlobalScenario): global scenario
        global_node (GlobalNode): global node representing the cluster

    Returns:
        ClusterSystem: cluster system
    """

    cluster_sys = ClusterSystem()
    cluster_sys.real_scenario = system.scenario
    cluster_sys.scenario = ClusterScenario.from_global_scenario(global_scenario, global_node)
    cluster_sys.sampling_time = system.sampling_time
    cluster_sys.time = system.time

    for app in system.apps:
        for real_node in global_node.nodes:
            cluster_sys.app_queue_size[app.id][real_node.id] = system.app_queue_size[app.id][real_node.id]
            cluster_sys.processing_delay[app.id][real_node.id] = system.processing_delay[app.id][real_node.id]

    if system.control_input is not None:
        cluster_sys.control_input = ClusterControlInput.from_real_control_input(system.control_input,
                                                                                global_scenario, global_node)
    if system.environment_input is not None:
        cluster_sys.environment_input = ClusterEnvironmentInput.from_real_environment_input(system.environment_input,
                                                                                            global_scenario,
                                                                                            global_node, system,
                                                                                            system.control_input)

    return cluster_sys
