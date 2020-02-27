from statistics import mean


def avg_unavailability(system, solution):
    probs = _calc_unavailability_probability(system, solution)
    return mean(probs) if len(probs) > 0 else 0.0


def avg_availability(system, solution):
    probs = _calc_unavailability_probability(system, solution)
    return mean(map(lambda p: 1.0 - p, probs)) if len(probs) > 0 else 0.0


def max_unavailability(system, solution):
    probs = _calc_unavailability_probability(system, solution)
    return max(probs) if len(probs) > 0 else 0.0


def min_availability(system, solution):
    probs = _calc_unavailability_probability(system, solution)
    return min(map(lambda p: 1.0 - p, probs)) if len(probs) > 0 else 0.0


def _calc_unavailability_probability(system, solution):
    probs = []
    for app in system.apps:
        fail_prob = 1.0
        for node in system.nodes:
            if solution.app_placement[app.id][node.id]:
                fail_prob *= (1.0 - app.availability * node.availability)
        probs.append(fail_prob)
    return probs