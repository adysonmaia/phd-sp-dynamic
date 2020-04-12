from sp.core.model import Resource
from statistics import mean


def overall_power_consumption(system, control_input, environment_input):
    values = _calc_cpu_power_consumption(system, control_input, environment_input)
    return sum(values) if len(values) > 0 else 0.0


def avg_power_consumption(system, control_input, environment_input):
    values = _calc_cpu_power_consumption(system, control_input, environment_input)
    return mean(values) if len(values) > 0 else 0.0


def max_power_consumption(system, control_input, environment_input):
    values = _calc_cpu_power_consumption(system, control_input, environment_input)
    return max(values) if len(values) > 0 else 0.0


def _calc_cpu_power_consumption(system, control_input, environment_input):
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
