from sp.hierarchical_controller.global_ctrl.model import GlobalSystem, GlobalControlInput, GlobalEnvironmentInput
from statistics import mean


def overall_cost(system, control_input, environment_input):
    """Overall Allocation Cost Metric

    Args:
        system (GlobalSystem): system
        control_input (GlobalControlInput): control input
        environment_input (GlobalEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    costs = _calc_resource_allocation_cost(system, control_input, environment_input)
    return sum(costs) if len(costs) > 0 else 0.0


def max_cost(system, control_input, environment_input):
    """Maximum Allocation Cost Metric

    Args:
        system (GlobalSystem): system
        control_input (GlobalControlInput): control input
        environment_input (GlobalEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    costs = _calc_resource_allocation_cost(system, control_input, environment_input)
    return max(costs) if len(costs) > 0 else 0.0


def avg_cost(system, control_input, environment_input):
    """Average Allocation Cost Metric

    Args:
        system (GlobalSystem): system
        control_input (GlobalControlInput): control input
        environment_input (GlobalEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    costs = _calc_resource_allocation_cost(system, control_input, environment_input)
    return mean(costs) if len(costs) > 0 else 0.0


def _calc_resource_allocation_cost(system, control_input, environment_input):
    """Calculate resource allocation cost for every application instance placed on nodes

    Args:
        system (GlobalSystem): system
        control_input (GlobalControlInput): control input
        environment_input (GlobalEnvironmentInput):  environment input
    Returns:
        list: list of metric values
    """
    costs = []
    for app in system.apps:
        for node in system.nodes:
            nb_instances = control_input.app_placement[app.id][node.id]
            if nb_instances <= 0:
                continue
            cost = 0.0
            for resource in system.resources:
                alloc_resource = control_input.allocated_resource[app.id][node.id][resource.name]
                cost += nb_instances * node.cost[resource.name](alloc_resource)
            if system.sampling_time > 0.0:
                cost *= system.sampling_time
            costs.append(cost)
    return costs
