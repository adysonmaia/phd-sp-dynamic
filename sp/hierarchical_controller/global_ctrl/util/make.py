from sp.hierarchical_controller.global_ctrl.model import GlobalSystem, GlobalControlInput, GlobalEnvironmentInput
from .calc import calc_load_after_distribution
import math


def make_global_limits(system, control_input, environment_input):
    """Specify the limits constraints imposed on subsystem controllers

    Args:
        system (GlobalSystem): system
        control_input (GlobalControlInput): control input
        environment_input (GlobalEnvironmentInput): environment input

    Returns:
        GlobalControlInput: control input
    """
    cloud_node = system.cloud_node
    for app in system.apps:
        for src_node in system.nodes:
            min_nb_instances = 0
            max_nb_instances = control_input.app_placement[app.id][src_node.id]
            if src_node == cloud_node:
                min_nb_instances = 1
                max_nb_instances = max(1, max_nb_instances)
            control_input.min_app_placement[app.id][src_node.id] = min_nb_instances
            control_input.max_app_placement[app.id][src_node.id] = max_nb_instances

            for dst_node in system.nodes:
                max_load = 0.0
                if src_node == dst_node or dst_node == cloud_node:
                    max_load = math.inf
                else:
                    max_load = calc_load_after_distribution(app.id, src_node.id, dst_node.id,
                                                            system, control_input, environment_input,
                                                            per_instance=False)
                control_input.max_load[app.id][src_node.id][dst_node.id] = max_load
    return control_input
