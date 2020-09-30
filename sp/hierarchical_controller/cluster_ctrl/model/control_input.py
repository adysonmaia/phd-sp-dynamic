from sp.core.model import ControlInput
from sp.system_controller.model.opt_solution import OptSolution
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalNode


class ClusterControlInput(OptSolution):
    """Cluster Control Input

    """

    @staticmethod
    def from_real_control_input(control_input, global_scenario, global_node):
        """Create cluster control input from real control input

        Args:
            control_input (ControlInput): real control input
            global_scenario (GlobalScenario): global scenario
            global_node (GlobalNode): global node representing the cluster

        Returns:
            ClusterControlInput: cluster control input
        """
        return from_real_control_input(control_input, global_scenario, global_node)


def from_real_control_input(control_input, global_scenario, global_node):
    """Create cluster control input from real control input

    Args:
        control_input (ControlInput): real control input
        global_scenario (GlobalScenario): global scenario
        global_node (GlobalNode): global node representing the cluster

    Returns:
        ClusterControlInput: cluster control input
    """
    c_ctrl_input = ClusterControlInput()
    real_scenario = global_scenario.real_scenario

    external_nodes = [ext_node for ext_node in global_scenario.network.nodes if ext_node != global_node]
    all_nodes = external_nodes + global_node.nodes

    # Initialization
    for app in real_scenario.apps:
        c_ctrl_input.app_placement[app.id] = {}
        c_ctrl_input.allocated_resource[app.id] = {}
        c_ctrl_input.load_distribution[app.id] = {}
        c_ctrl_input.received_load[app.id] = {}
        for node in all_nodes:
            c_ctrl_input.app_placement[app.id][node.id] = False
            c_ctrl_input.received_load[app.id][node.id] = 0.0
            c_ctrl_input.allocated_resource[app.id][node.id] = {}
            c_ctrl_input.load_distribution[app.id][node.id] = {}
            for resource in real_scenario.resources:
                c_ctrl_input.allocated_resource[app.id][node.id][resource.name] = 0.0
            for dst_node in all_nodes:
                c_ctrl_input.load_distribution[app.id][node.id][dst_node.id] = 0.0

    for app in real_scenario.apps:
        # For nodes inside the cluster
        for real_node in global_node.nodes:
            # Placement
            place = control_input.app_placement[app.id][real_node.id]
            c_ctrl_input.app_placement[app.id][real_node.id] = place

            # Resource allocation
            for resource in real_scenario.resources:
                alloc = control_input.allocated_resource[app.id][real_node.id][resource.name]
                c_ctrl_input.allocated_resource[app.id][real_node.id][resource.name] = alloc

            # Received load cache
            c_ctrl_input.received_load[app.id][real_node.id] = 0.0
            if isinstance(control_input, OptSolution):
                load = control_input.received_load[app.id][real_node.id]
                c_ctrl_input.received_load[app.id][real_node.id] = load

            # Load distribution
            for real_dst_node in global_node.nodes:
                ld = control_input.load_distribution[app.id][real_node.id][real_dst_node.id]
                c_ctrl_input.load_distribution[app.id][real_node.id][real_dst_node.id] = ld

            # Load distribution from nodes inside the cluster to external clusters
            for ext_node in external_nodes:
                ld = 0.0
                for real_dst_node in ext_node.nodes:
                    ld += control_input.load_distribution[app.id][real_node.id][real_dst_node.id]
                c_ctrl_input.load_distribution[app.id][real_node.id][ext_node.id] = ld

        # For nodes outside the cluster
        for ext_node in external_nodes:
            place_count = 0
            for real_node in ext_node.nodes:
                place = control_input.app_placement[app.id][real_node.id]
                place_count += int(place)
            c_ctrl_input.app_placement[app.id][ext_node.id] = place_count > 0

            for resource in real_scenario.resources:
                alloc = 0
                for real_node in ext_node.nodes:
                    alloc += control_input.allocated_resource[app.id][real_node.id][resource.name]
                alloc = alloc / float(place_count) if place_count > 0 else 0.0
                c_ctrl_input.allocated_resource[app.id][ext_node.id][resource.name] = alloc

            c_ctrl_input.received_load[app.id][ext_node.id] = 0.0
            if isinstance(control_input, OptSolution):
                load = 0.0
                for real_node in ext_node.nodes:
                    load += control_input.received_load[app.id][real_node.id]
                load = load / float(place_count) if place_count > 0 else 0.0
                c_ctrl_input.received_load[app.id][ext_node.id] = load

            # TODO: load distribution from external cluster to nodes inside the cluster

    return c_ctrl_input

