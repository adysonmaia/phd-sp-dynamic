from sp.core.model import Resource
from statistics import mean


def overall_power_consumption(system, solution):
    values = _calc_cpu_power_consumption(system, solution)
    return sum(values) if len(values) > 0 else 0.0


def avg_power_consumption(system, solution):
    values = _calc_cpu_power_consumption(system, solution)
    return mean(values) if len(values) > 0 else 0.0


def max_power_consumption(system, solution):
    values = _calc_cpu_power_consumption(system, solution)
    return max(values) if len(values) > 0 else 0.0


def _calc_cpu_power_consumption(system, solution):
    consumptions = []
    for node in system.nodes:
        cpu_total = node.cpu_capacity
        cpu_used = 0.0
        for app in system.apps:
            if solution.app_placement[app.id][node.id]:
                cpu_used += solution.allocated_resource[app.id][node.id][Resource.CPU]

        utilization = cpu_used / float(cpu_total)
        pwr_cons = node.power_consumption(utilization)
        consumptions.append(pwr_cons)
    return consumptions
