from statistics import mean


def overall_cost(system, solution):
    costs = _calc_resource_allocation_cost(system, solution)
    return sum(costs) if len(costs) > 0 else 0.0


def max_cost(system, solution):
    costs = _calc_resource_allocation_cost(system, solution)
    return max(costs) if len(costs) > 0 else 0.0


def avg_cost(system, solution):
    costs = _calc_resource_allocation_cost(system, solution)
    return mean(costs) if len(costs) > 0 else 0.0


def _calc_resource_allocation_cost(system, solution):
    costs = []
    for app in system.apps:
        for node in system.nodes:
            if not solution.app_placement[app.id][node.id]:
                continue
            cost = 0.0
            for resource in system.resources:
                alloc_resource = solution.allocated_resource[app.id][node.id][resource.name]
                cost += node.cost[resource.name](alloc_resource)
            costs.append(cost)
    return costs
