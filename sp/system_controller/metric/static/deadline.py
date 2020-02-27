from sp.system_controller.utils.opt import calc_processing_delay, calc_network_delay
from statistics import mean


def max_deadline_violation(system, solution):
    delta = _calc_delta_time(system, solution)
    violations = list(filter(lambda d: d > 0.0, delta))
    return max(violations) if len(violations) > 0 else 0.0


def avg_deadline_violation(system, solution):
    delta = _calc_delta_time(system, solution)
    violations = list(filter(lambda d: d > 0.0, delta))
    return mean(violations) if len(violations) > 0 else 0.0


def deadline_satisfaction(system, solution):
    delta = _calc_delta_time(system, solution)
    success_count = sum(map(lambda d: d <= 0.0, delta))
    return success_count / float(len(delta))


def _calc_delta_time(system, solution):
    delta = []

    for app in system.apps:
        for dst_node in system.nodes:
            if not solution.app_placement[app.id][dst_node.id]:
                continue

            proc_delay = calc_processing_delay(app, dst_node, system, solution)

            for src_node in system.nodes:
                load = system.get_request_load(app.id, src_node.id)
                ld = solution.load_distribution[app.id][src_node.id][dst_node.id]
                if load == 0.0 or ld == 0.0:
                    continue

                net_delay = calc_network_delay(app, src_node, dst_node, system, solution)
                delay = net_delay + proc_delay
                delta.append(delay - app.deadline)

    return delta

