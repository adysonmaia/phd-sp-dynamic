from sp.core.model import System, ControlInput, EnvironmentInput
from statistics import mean


def avg_unavailability(system, control_input, environment_input):
    """Average Unavailability Metric

    Args:
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput):  environment input
    Returns:
        float: metric value
    """

    probs = _calc_unavailability_probability(system, control_input, environment_input)
    return mean(probs) if len(probs) > 0 else 0.0


def avg_availability(system, control_input, environment_input):
    """Average Availability Metric

    Args:
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    probs = _calc_unavailability_probability(system, control_input, environment_input)
    return mean(map(lambda p: 1.0 - p, probs)) if len(probs) > 0 else 0.0


def max_unavailability(system, control_input, environment_input):
    """Maximum Unavailability Metric

    Args:
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    probs = _calc_unavailability_probability(system, control_input, environment_input)
    return max(probs) if len(probs) > 0 else 0.0


def min_availability(system, control_input, environment_input):
    """Minimum Availability Metric

    Args:
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput):  environment input
    Returns:
        float: metric value
    """
    probs = _calc_unavailability_probability(system, control_input, environment_input)
    return min(map(lambda p: 1.0 - p, probs)) if len(probs) > 0 else 0.0


def _calc_unavailability_probability(system, control_input, environment_input):
    """Calculate unavailability for every application place on nodes

    Args:
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput):  environment input
    Returns:
        list: list of metric values
    """
    probs = []
    for app in system.apps:
        fail_prob = 1.0
        for node in system.nodes:
            if control_input.app_placement[app.id][node.id]:
                fail_prob *= (1.0 - app.availability * node.availability)
        probs.append(fail_prob)
    return probs
