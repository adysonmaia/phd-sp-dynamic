from sp.core.model import System, ControlInput, EnvironmentInput
from sp.system_controller.model import OptSolution
from sp.system_controller.util.calc import calc_received_load
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario
from sp.hierarchical_controller.cluster_ctrl.model import ClusterControlInput
import copy


def make_real_control_input(system, environment_input, cluster_control_inputs, global_scenario):
    """Make real control input from control inputs of each cluster (subsystem)

    Args:
        system (System): real system
        environment_input (EnvironmentInput): real environment input
        cluster_control_inputs (dict): control input for each cluster. It is indexed by cluster's id
        global_scenario (GlobalScenario): global scenario

    Returns:
        ControlInput: real control input
    """
    ctrl_input = OptSolution.create_empty(system)
    cloud_node = system.cloud_node

    for app in system.apps:
        for global_node in global_scenario.network.nodes:
            cluster_ctrl_input = cluster_control_inputs[global_node.id]

            for real_node in global_node.nodes:
                place = cluster_ctrl_input.app_placement[app.id][real_node.id]
                alloc = cluster_ctrl_input.allocated_resource[app.id][real_node.id]
                load = cluster_ctrl_input.received_load[app.id][real_node.id]

                # Set placement and resource allocation
                ctrl_input.app_placement[app.id][real_node.id] = place
                ctrl_input.allocated_resource[app.id][real_node.id] = copy.deepcopy(alloc)
                ctrl_input.received_load[app.id][real_node.id] = load

                total_ld = 0.0
                # Set load distribution inside the cluster
                for real_dst_node in global_node.nodes:
                    ld = cluster_ctrl_input.load_distribution[app.id][real_node.id][real_dst_node.id]
                    ctrl_input.load_distribution[app.id][real_node.id][real_dst_node.id] = ld
                    total_ld += ld

                # Set load distribution to outside of the cluster
                for ext_node in global_scenario.network.nodes:
                    if global_node == ext_node:
                        continue

                    ld = cluster_ctrl_input.load_distribution[app.id][real_node.id][ext_node.id]
                    if ld > 0.0:
                        ext_ctrl_input = cluster_control_inputs[ext_node.id]
                        for real_dst_node in ext_node.nodes:
                            ext_ld = ext_ctrl_input.load_distribution[app.id][global_node.id][real_dst_node.id]
                            ctrl_input.load_distribution[app.id][real_node.id][real_dst_node.id] = ld * ext_ld
                            total_ld += ld * ext_ld

                # Set remaining load to cloud
                cloud_ld = ctrl_input.load_distribution[app.id][real_node.id][cloud_node.id]
                cloud_ld += 1.0 - total_ld
                ctrl_input.load_distribution[app.id][real_node.id][cloud_node.id] = cloud_ld

        # Calculate and cache received load
        for node in system.nodes:
            load = calc_received_load(app.id, node.id, system, ctrl_input, environment_input, use_cache=False)
            ctrl_input.received_load[app.id][node.id] = load

        # Allocate resource for cloud
        for resource in system.resources:
            load = ctrl_input.received_load[app.id][cloud_node.id]
            alloc = app.demand[resource.name](load)
            ctrl_input.allocated_resource[app.id][cloud_node.id][resource.name] = alloc

    return ctrl_input
