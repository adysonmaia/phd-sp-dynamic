from statistics import mean


def overall_cost(system, control_input, environment_input):
    costs = _calc_resource_allocation_cost(system, control_input, environment_input)
    return sum(costs) if len(costs) > 0 else 0.0


def max_cost(system, control_input, environment_input):
    costs = _calc_resource_allocation_cost(system, control_input, environment_input)
    return max(costs) if len(costs) > 0 else 0.0


def avg_cost(system, control_input, environment_input):
    costs = _calc_resource_allocation_cost(system, control_input, environment_input)
    return mean(costs) if len(costs) > 0 else 0.0


def _calc_resource_allocation_cost(system, control_input, environment_input):
    costs = []
    for app in system.apps:
        for node in system.nodes:
            if not control_input.app_placement[app.id][node.id]:
                continue
            cost = 0.0
            for resource in system.resources:
                alloc_resource = control_input.allocated_resource[app.id][node.id][resource.name]
                cost += node.cost[resource.name](alloc_resource)
            costs.append(cost)
    return costs
