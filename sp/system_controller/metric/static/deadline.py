from sp.system_controller.estimator.processing import DefaultProcessingEstimator
from sp.system_controller.utils import calc_load_before_distribution
from statistics import mean


def max_deadline_violation(system, control_input, environment_input):
    delta = _calc_delta_time(system, control_input, environment_input)
    violations = list(filter(lambda d: d > 0.0, delta))
    return max(violations) if len(violations) > 0 else 0.0


def avg_deadline_violation(system, control_input, environment_input):
    delta = _calc_delta_time(system, control_input, environment_input)
    violations = list(filter(lambda d: d > 0.0, delta))
    return mean(violations) if len(violations) > 0 else 0.0


def deadline_satisfaction(system, control_input, environment_input):
    delta = _calc_delta_time(system, control_input, environment_input)
    success_count = sum(map(lambda d: d <= 0.0, delta))
    return success_count / float(len(delta))


def _calc_delta_time(system, control_input, environment_input):
    proc_estimator = DefaultProcessingEstimator()

    delta = []
    for app in system.apps:
        for dst_node in system.nodes:
            if not control_input.get_app_placement(app.id, dst_node.id):
                continue

            proc_result = proc_estimator(app.id, dst_node.id,
                                         system=system,
                                         control_input=control_input,
                                         environment_input=environment_input)
            proc_delay = proc_result.delay

            for src_node in system.nodes:
                ld = control_input.get_load_distribution(app.id, src_node.id, dst_node.id)
                load = calc_load_before_distribution(app.id, src_node.id, system, environment_input)
                load = load * ld
                if load > 0.0:
                    net_delay = environment_input.get_net_delay(app.id, src_node.id, dst_node.id)
                    delay = net_delay + proc_delay
                    delta.append(delay - app.deadline)
    return delta

