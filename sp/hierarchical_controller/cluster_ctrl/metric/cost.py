from sp.hierarchical_controller.global_ctrl.model import GlobalNode
from sp.hierarchical_controller.cluster_ctrl.model import ClusterSystem, ClusterControlInput, ClusterEnvironmentInput
from statistics import mean


def overall_cost(system, control_input, environment_input):
    """Overall Allocation Cost Metric

    Args:
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    costs = _calc_resource_allocation_cost(system, control_input, environment_input)
    return sum(costs) if len(costs) > 0 else 0.0


def max_cost(system, control_input, environment_input):
    """Maximum Allocation Cost Metric

    Args:
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    costs = _calc_resource_allocation_cost(system, control_input, environment_input)
    return max(costs) if len(costs) > 0 else 0.0


def avg_cost(system, control_input, environment_input):
    """Average Allocation Cost Metric

    Args:
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    costs = _calc_resource_allocation_cost(system, control_input, environment_input)
    return mean(costs) if len(costs) > 0 else 0.0


def _calc_resource_allocation_cost(system, control_input, environment_input):
    """Calculate resource allocation cost for every application instance placed on nodes

    Args:
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
    Returns:
        list: list of metric values
    """
    costs = []
    for app in system.apps:
        # TODO: calculate only for internal nodes?
        for node in system.nodes:
            if not control_input.app_placement[app.id][node.id]:
                continue
            nb_instances = 1
            if isinstance(node, GlobalNode):
                nb_instances = environment_input.get_nb_instances(app.id, node.id)
                nb_instances = int(max(1, nb_instances))

            cost = 0.0
            for resource in system.resources:
                alloc_resource = control_input.allocated_resource[app.id][node.id][resource.name]
                # TODO: is this multiplication by number of instances really necessary?
                cost += nb_instances * node.cost[resource.name](alloc_resource)
            if system.sampling_time > 0.0:
                cost *= system.sampling_time
            costs.append(cost)
    return costs
