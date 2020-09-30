from sp.core.model import ControlInput
from sp.system_controller.model.opt_solution import OptSolution
from .scenario import GlobalScenario
from collections import defaultdict


class GlobalControlInput(OptSolution):
    """Global Control Input

    """

    def __init__(self):
        """Initialization
        """
        OptSolution.__init__(self)
        self.max_app_placement = defaultdict(lambda: defaultdict(int))
        self.min_app_placement = defaultdict(lambda: defaultdict(int))
        self.max_load = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

    def get_max_app_placement(self, app_id, node_id):
        """Get max number of instances in a global node

        Args:
            app_id (int): application's id
            node_id (int): node's id

        Returns:
            int: max. number of instances
        """
        return self.max_app_placement[app_id][node_id]

    def get_min_app_placement(self, app_id, node_id):
        """Get min number of instances in a global node

        Args:
            app_id (int): application's id
            node_id (int): node's id

        Returns:
            int: min. number of instances
        """
        return self.min_app_placement[app_id][node_id]

    def get_max_load(self, app_id, src_node_id, dst_node_id):
        """Get max. load dispatched from a source node to a destination node

        Args:
            app_id (int): application's id
            src_node_id (int): source node's id
            dst_node_id (int): destination node's id

        Returns:
            float: max. load
        """
        return self.max_load[app_id][src_node_id][dst_node_id]

    @classmethod
    def create_empty(cls, system):
        """Create a empty solution for a system's scenario

        Args:
            system (sp.hierarchical_controller.global_ctrl.model.system.System): system

        Returns:
            GlobalControlInput: solution
        """
        ctrl = super(GlobalControlInput, cls).create_empty(system)
        ctrl.app_placement = defaultdict(lambda: defaultdict(int))
        return ctrl

    @staticmethod
    def from_real_control_input(control_input, global_scenario):
        """Create global control input from real input

        Args:
            control_input (ControlInput): real control input
            global_scenario (GlobalScenario): global scenario

        Returns:
            GlobalControlInput: global control input
        """
        return from_real_control_input(control_input, global_scenario)


def from_real_control_input(control_input, global_scenario):
    """Create global control input from real input

    Args:
        control_input (ControlInput): real control input
        global_scenario (GlobalScenario): global scenario

    Returns:
        GlobalControlInput: global control input
    """

    global_ctrl_input = GlobalControlInput()

    # Initialization
    global_ctrl_input.app_placement = defaultdict(lambda: defaultdict(int))
    global_ctrl_input.allocated_resource = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    global_ctrl_input.load_distribution = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    global_ctrl_input.received_load = defaultdict(lambda: defaultdict(float))

    for app in global_scenario.apps:
        for global_node in global_scenario.network.nodes:
            place_count = 0
            alloc = defaultdict(float)
            load = 0.0

            for real_node in global_node.nodes:
                place_count += int(control_input.app_placement[app.id][real_node.id])
                if isinstance(control_input, OptSolution):
                    load += control_input.received_load[app.id][real_node.id]
                for resource in global_scenario.resources:
                    alloc[resource.name] += control_input.allocated_resource[app.id][real_node.id][resource.name]

            if place_count > 0:
                global_ctrl_input.app_placement[app.id][global_node.id] = place_count
                for resource in global_scenario.resources:
                    avg_alloc = alloc[resource.name] / float(place_count)
                    global_ctrl_input.allocated_resource[app.id][global_node.id][resource.name] = avg_alloc
                global_ctrl_input.received_load[app.id][global_node.id] = load / float(place_count)

    # TODO: set load distribution

    return global_ctrl_input



