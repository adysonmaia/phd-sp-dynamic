from sp.core.model import Resource, System, ControlInput, EnvironmentInput
from statistics import mean


def overall_power_consumption(system, control_input, environment_input):
    """Overall CPU Power Consumption Metric

    Args:
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    values = _calc_cpu_power_consumption(system, control_input, environment_input)
    return sum(values) if len(values) > 0 else 0.0


def avg_power_consumption(system, control_input, environment_input):
    """Average CPU Power Consumption Metric

    Args:
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    values = _calc_cpu_power_consumption(system, control_input, environment_input)
    return mean(values) if len(values) > 0 else 0.0


def max_power_consumption(system, control_input, environment_input):
    """Maximum CPU Power Consumption Metric

    Args:
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    values = _calc_cpu_power_consumption(system, control_input, environment_input)
    return max(values) if len(values) > 0 else 0.0


def _calc_cpu_power_consumption(system, control_input, environment_input):
    """ Calculate CPU power consumption for every nodes

    Args:
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput):  environment input
    Returns:
        list: list of metric values
    """
    consumptions = []
    for node in system.nodes:
        cpu_total = node.cpu_capacity
        cpu_used = 0.0
        for app in system.apps:
            if control_input.app_placement[app.id][node.id]:
                cpu_used += control_input.allocated_resource[app.id][node.id][Resource.CPU]

        utilization = cpu_used / float(cpu_total) if cpu_total > 0.0 else 0.0
        pwr_cons = node.power_consumption(utilization)
        consumptions.append(pwr_cons)
    return consumptions
