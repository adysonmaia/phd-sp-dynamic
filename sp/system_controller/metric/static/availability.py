from statistics import mean


def avg_unavailability(system, solution):
    probs = _calc_unavailability_probability(system, solution)
    return mean(probs)


def avg_availability(system, solution):
    probs = _calc_unavailability_probability(system, solution)
    probs = map(lambda p: 1.0 - p, probs)
    return mean(probs)


def max_unavailability(system, solution):
    probs = _calc_unavailability_probability(system, solution)
    return max(probs)


def min_availability(system, solution):
    probs = _calc_unavailability_probability(system, solution)
    probs = map(lambda p: 1.0 - p, probs)
    return min(probs)


def _calc_unavailability_probability(system, solution):
    probs = []
    for app in system.apps:
        fail_prob = 1.0
        for node in system.nodes:
            if solution.app_placement[app.id][node.id]:
                fail_prob *= (1.0 - app.availability * node.availability)
        probs.append(fail_prob)
    return probs