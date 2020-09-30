from sp.hierarchical_controller.cluster_ctrl.model import ClusterSystem, ClusterControlInput, ClusterEnvironmentInput
from sp.hierarchical_controller.cluster_ctrl.util.calc import calc_response_time, calc_load_after_distribution
from numpy import mean, average


def max_deadline_violation(system, control_input, environment_input):
    """Maximum Deadline Violation Metric

    Args:
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    delta = _calc_delta_time(system, control_input, environment_input)
    violations = list(filter(lambda d: d > 0.0, delta))
    return max(violations) if len(violations) > 0 else 0.0


def avg_deadline_violation(system, control_input, environment_input):
    """Average Deadline Violation Metric

    Args:
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    delta = _calc_delta_time(system, control_input, environment_input)
    violations = list(map(lambda d: max(0.0, d), delta))
    return mean(violations) if len(violations) > 0 else 0.0


def weighted_avg_deadline_violation(system, control_input, environment_input):
    """Weighted Average Deadline Violation Metric

    Args:
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    delta, load = _calc_delta_time(system, control_input, environment_input, return_load=True)
    violations = list(map(lambda d: max(0.0, d), delta))
    total_load = sum(load) if len(load) > 0 else 0.0
    if len(violations) > 0 and total_load > 0.0:
        return average(violations, weights=load)
    else:
        return 0.0


def avg_only_violated_deadline(system, control_input, environment_input):
    """Average Only Violated Deadline Metric

    Args:
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    delta = _calc_delta_time(system, control_input, environment_input)
    violations = list(filter(lambda d: d > 0.0, delta))
    return mean(violations) if len(violations) > 0 else 0.0


def weighted_avg_only_violated_deadline(system, control_input, environment_input):
    """Average Only Violated Deadline Metric

    Args:
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    delta, load = _calc_delta_time(system, control_input, environment_input, return_load=True)
    filtered_index = list(filter(lambda i: delta[i] > 0.0, range(len(delta))))
    violations = [delta[i] for i in filtered_index]
    load = [load[i] for i in filtered_index]
    total_load = sum(load) if len(load) > 0 else 0.0
    if len(violations) > 0 and total_load > 0.0:
        return average(violations, weights=load)
    else:
        return 0.0


def overall_deadline_violation(system, control_input, environment_input):
    """Overall Deadline Violation Metric

    Args:
        system (ClusterSystem ): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    delta = _calc_delta_time(system, control_input, environment_input)
    violations = list(filter(lambda d: d > 0.0, delta))
    return sum(violations) if len(violations) > 0 else 0.0


def weighted_overall_deadline_violation(system, control_input, environment_input):
    """Weighted Overall Deadline Violation Metric

    Args:
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    delta, load = _calc_delta_time(system, control_input, environment_input, return_load=True)
    violations = list(map(lambda i: max(delta[i], 0.0) * load[i], range(len(delta))))
    return sum(violations) if len(violations) > 0 else 0.0


def deadline_satisfaction(system, control_input, environment_input):
    """Deadline Satisfaction Rate Metric

    Args:
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    delta = _calc_delta_time(system, control_input, environment_input)
    success_count = sum(map(lambda d: d <= 0.0, delta))
    return success_count / float(len(delta)) if len(delta) > 0 else 1.0


def weighted_deadline_satisfaction(system, control_input, environment_input):
    """Weighted Deadline Satisfaction Rate Metric

    Args:
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    delta, load = _calc_delta_time(system, control_input, environment_input, return_load=True)
    sat = list(map(lambda i: load[i] if delta[i] <= 0.0 else 0.0, range(len(delta))))
    total_load = sum(load) if len(load) > 0 else 0.0
    return sum(sat) / total_load if len(sat) > 0 and total_load > 0.0 else 0.0


def _calc_delta_time(system, control_input, environment_input, return_load=False):
    """Calculate difference between response time and deadline for all request flows

    Args:
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput):  environment input
        return_load (bool): Return along with time deltas, the loads of each request flow
    Returns:
        Union[list, tuple]: lists of time deltas or a tuple with time deltas and loads
    """
    deltas, loads = [], []
    for app in system.apps:
        for dst_node in system.nodes:
            if not control_input.get_app_placement(app.id, dst_node.id):
                continue
            for src_node in system.nodes:
                load = calc_load_after_distribution(app.id, src_node.id, dst_node.id,
                                                    system, control_input, environment_input,
                                                    per_instance=False)
                if load > 0.0:
                    rt = calc_response_time(app.id, src_node.id, dst_node.id,
                                            system, control_input, environment_input)
                    deltas.append(rt - app.deadline)
                    loads.append(load)
    if return_load:
        return deltas, loads
    else:
        return deltas
