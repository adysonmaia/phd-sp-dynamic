from statistics import mean


def avg_unavailability(system, control_input, environment_input):
    probs = _calc_unavailability_probability(system, control_input, environment_input)
    return mean(probs) if len(probs) > 0 else 0.0


def avg_availability(system, control_input, environment_input):
    probs = _calc_unavailability_probability(system, control_input, environment_input)
    return mean(map(lambda p: 1.0 - p, probs)) if len(probs) > 0 else 0.0


def max_unavailability(system, control_input, environment_input):
    probs = _calc_unavailability_probability(system, control_input, environment_input)
    return max(probs) if len(probs) > 0 else 0.0


def min_availability(system, control_input, environment_input):
    probs = _calc_unavailability_probability(system, control_input, environment_input)
    return min(map(lambda p: 1.0 - p, probs)) if len(probs) > 0 else 0.0


def _calc_unavailability_probability(system, control_input, environment_input):
    probs = []
    for app in system.apps:
        fail_prob = 1.0
        for node in system.nodes:
            if control_input.app_placement[app.id][node.id]:
                fail_prob *= (1.0 - app.availability * node.availability)
        probs.append(fail_prob)
    return probs