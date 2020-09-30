from sp.core.model.environment_input import EnvironmentInput
from .scenario import GlobalScenario
from statistics import mean


class GlobalEnvironmentInput(EnvironmentInput):
    """Global Environment Input Model Class

    Attributes:
        real_environment_input (EnvironmentInput): real environment input
    """

    def __init__(self):
        """Initialisation
        """
        EnvironmentInput.__init__(self)
        self.real_environment_input = None

    def __copy__(self):
        """Shallow copy

        Returns:
            GlobalEnvironmentInput: the shallow copy
        """
        cp = EnvironmentInput.__copy__(self)
        cp.real_environment_input = self.real_environment_input
        return cp

    @classmethod
    def create_empty(cls, system):
        """Create an empty environment input based on a system's state

        Args:
            system (sp.hierarchical_controller.global_ctrl.model.system.GlobalSystem): system's state
        Returns:
            GlobalEnvironmentInput: an empty environment input
        """
        env = super(GlobalEnvironmentInput, cls).create_empty(system)
        return env

    @staticmethod
    def from_real_environment_inputs(environment_inputs, global_scenario):
        """Create global environment input from real environment inputs

        Args:
            environment_inputs (Union[list, EnvironmentInput]): list of real environment
                inputs or a single real environment input
            global_scenario (GlobalScenario): global scenario

        Returns:
            GlobalEnvironmentInput: global environment input
        """
        return from_real_environment_inputs(environment_inputs, global_scenario)


def from_real_environment_inputs(environment_inputs, global_scenario):
    """Create global environment input from real environment inputs

    Args:
        environment_inputs (Union[list, EnvironmentInput]): list of real environment
            inputs or a single real environment input
        global_scenario (GlobalScenario): global scenario

    Returns:
        GlobalEnvironmentInput: global environment input
    """
    apps = global_scenario.apps
    global_nodes = global_scenario.network.nodes
    global_env = GlobalEnvironmentInput()

    if not isinstance(environment_inputs, list):
        environment_inputs = [environment_inputs]

    if len(environment_inputs) > 0:
        global_env.real_environment_input = environment_inputs[0]

    for app in apps:
        global_env.generated_load[app.id] = {}
        global_env.net_delay[app.id] = {}
        global_env.net_path[app.id] = {}

        for global_node in global_nodes:
            global_env.net_delay[app.id][global_node.id] = {}
            global_env.net_path[app.id][global_node.id] = {}

            # Avg delay inside the cluster
            loads = []
            delays = []
            for real_node in global_node.nodes:
                for env_input in environment_inputs:
                    loads.append(env_input.get_generated_load(app.id, real_node.id))
                    delays.append(env_input.get_net_delay(app.id, global_node.central_node.id, real_node.id))
            avg_load = mean(loads) if len(loads) > 0 else 0.0
            avg_delay = mean(delays) if len(delays) > 0 else 0.0

            global_env.generated_load[app.id][global_node.id] = avg_load
            global_env.net_delay[app.id][global_node.id][global_node.id] = avg_delay
            global_env.net_path[app.id][global_node.id][global_node.id] = []

    for app in apps:
        for src_global_node in global_nodes:
            for dst_global_node in global_nodes:
                if src_global_node == dst_global_node:
                    continue

                # Avg delay between different clusters
                delays = [e.get_net_delay(app.id, src_global_node.central_node.id, dst_global_node.central_node.id)
                          for e in environment_inputs]
                avg_delay = mean(delays) if len(delays) > 0 else 0.0
                global_env.net_delay[app.id][src_global_node.id][dst_global_node.id] = avg_delay
                global_env.net_path[app.id][src_global_node.id][dst_global_node.id] = None

                if len(environment_inputs) > 0:
                    env_input = global_env.real_environment_input
                    src_real_node = src_global_node.central_node
                    dst_real_node = dst_global_node.central_node
                    path = env_input.get_net_path(app.id, src_real_node.id, dst_real_node.id)
                    global_env.net_path[app.id][src_global_node.id][dst_global_node.id] = path

    return global_env
