from sp.system_controller.util import calc_response_time, calc_load_after_distribution
from statistics import mean


def max_deadline_violation(system, control_input, environment_input):
    delta = _calc_delta_time(system, control_input, environment_input)
    violations = list(filter(lambda d: d > 0.0, delta))
    return max(violations) if len(violations) > 0 else 0.0


def avg_deadline_violation(system, control_input, environment_input):
    delta = _calc_delta_time(system, control_input, environment_input)
    violations = list(filter(lambda d: d > 0.0, delta))
    return mean(violations) if len(violations) > 0 else 0.0


def overall_deadline_violation(system, control_input, environment_input):
    delta = _calc_delta_time(system, control_input, environment_input)
    violations = list(filter(lambda d: d > 0.0, delta))
    return sum(violations) if len(violations) > 0 else 0.0


def deadline_satisfaction(system, control_input, environment_input):
    delta = _calc_delta_time(system, control_input, environment_input)
    success_count = sum(map(lambda d: d <= 0.0, delta))
    return success_count / float(len(delta)) if len(delta) > 0 else 1.0


def _calc_delta_time(system, control_input, environment_input):
    delta = []
    for app in system.apps:
        for dst_node in system.nodes:
            if not control_input.get_app_placement(app.id, dst_node.id):
                continue
            for src_node in system.nodes:
                load = calc_load_after_distribution(app.id, src_node.id, dst_node.id,
                                                    system, control_input, environment_input)
                if load > 0.0:
                    rt = calc_response_time(app.id, src_node.id, dst_node.id,
                                            system, control_input, environment_input)
                    delta.append(rt - app.deadline)
    return delta

