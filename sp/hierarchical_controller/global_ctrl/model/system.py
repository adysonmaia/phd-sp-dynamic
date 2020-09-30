from sp.core.model import System, Scenario, Node
from .scenario import GlobalScenario
from .control_input import GlobalControlInput
from .environment_input import GlobalEnvironmentInput
from statistics import mean


class GlobalSystem(System):
    """Global System Model Class

    Attributes:
        real_system (System): real system
        real_scenario (Scenario): real scenario
    """

    def __init__(self):
        """Initialization
        """
        System.__init__(self)
        self.real_system = None
        self.real_scenario = None

    def __copy__(self):
        """Shallow copy

        Returns:
            GlobalSystem: the shallow copy
        """
        cp = System.__copy__(self)
        cp.real_system = self.real_system
        cp.real_scenario = self.real_scenario
        return cp

    def clear_copy(self):
        """Copy system's state with its (control and environment) inputs undefined

        Returns:
            GlobalSystem: an empty system's state
        """
        cp = System.clear_copy(self)
        cp.real_system = self.real_system
        cp.real_scenario = self.real_scenario
        return cp

    @property
    def real_nodes(self):
        """Get all real nodes of the system's scenario

        Returns:
            list(Node): list of nodes
        """
        if self.real_scenario is None:
            return []
        else:
            return self.real_scenario.network.nodes

    @staticmethod
    def from_real_systems(systems, global_scenario):
        """Create global_ctrl system's state from real system's states

        Args:
            systems (Union[list, System]): real system's states
            global_scenario (GlobalScenario): global scenario

        Returns:
            GlobalSystem: global system
        """
        return from_real_systems(systems, global_scenario)


def from_real_systems(systems, global_scenario):
    """Create global_ctrl system's state from real system's states

    Args:
        systems (Union[list, System]): real system's states
        global_scenario (GlobalScenario): global scenario

    Returns:
        GlobalSystem: global system
    """

    if not isinstance(systems, list):
        systems = [systems]

    global_system = GlobalSystem()
    if len(systems) > 0:
        last_system = systems[-1]
        global_system.real_system = last_system
        global_system.real_scenario = last_system.scenario
        global_system.scenario = global_scenario
        global_system.time = last_system.time
        global_system.sampling_time = len(systems) * last_system.sampling_time

        if last_system.control_input is not None:
            control_input = last_system.control_input
            env_input = last_system.environment_input
            global_system.control_input = GlobalControlInput.from_real_control_input(control_input, global_scenario)
            global_system.environment_input = GlobalEnvironmentInput.from_real_environment_inputs(env_input,
                                                                                                  global_scenario)

    for app in global_system.apps:
        for global_node in global_system.nodes:
            global_queue_size = []
            global_proc_delay = []

            for system in systems:
                if system.control_input is None:
                    continue

                queue_size = []
                proc_delay = []
                for real_node in global_node.nodes:
                    if system.control_input.get_app_placement(app.id, real_node.id):
                        queue_size.append(system.get_app_queue_size(app.id, real_node.id))
                        proc_delay.append(system.get_processing_delay(app.id, real_node.id))

                queue_size = mean(queue_size) if len(queue_size) > 0 else 0.0
                proc_delay = mean(proc_delay) if len(proc_delay) > 0 else 0.0
                global_queue_size.append(queue_size)
                global_proc_delay.append(proc_delay)

            global_queue_size = mean(global_queue_size) if len(global_queue_size) > 0 else 0.0
            global_proc_delay = mean(global_proc_delay) if len(global_proc_delay) > 0 else 0.0
            global_system.app_queue_size[app.id][global_node.id] = global_queue_size
            global_system.processing_delay[app.id][global_node.id] = global_proc_delay

    return global_system
