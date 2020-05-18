from sp.system_controller.util.calc import calc_load_before_distribution


ROUND_PRECISION = 5


def make_solution_feasible(system, solution, environment_input):
    """It tries to make a solution feasible

    Args:
        system (sp.core.model.system.System): system
        solution (sp.system_controller.model.opt_solution.OptSolution): optimization solution
        environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
    Returns:
        sp.system_controller.model.opt_solution.OptSolution: feasible solution
    """
    # solution = _round_values(system, solution, environment_input)
    solution = make_min_instances_constraint_feasible(system, solution, environment_input)
    solution = make_max_instances_constraint_feasible(system, solution, environment_input)
    solution = make_load_distribution_constraint_feasible(system, solution, environment_input)
    return solution


def make_min_instances_constraint_feasible(system, solution, environment_input):
    """Satisfy the constraint of minimum number of instances

    Args:
        system (sp.core.model.system.System): system
        solution (sp.system_controller.model.opt_solution.OptSolution): optimization solution
        environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
    Returns:
        sp.system_controller.model.opt_solution.OptSolution: feasible solution
    """
    cloud_node = system.cloud_node
    for app in system.apps:
        instances = [n for n in system.nodes if solution.app_placement[app.id][n.id]]
        if len(instances) > 0:
            continue

        load = 0.0
        solution.app_placement[app.id][cloud_node.id] = True
        solution.received_load[app.id][cloud_node.id] = load
        for resource in system.resources:
            demand = app.demand[resource.name](load)
            solution.allocated_resource[app.id][cloud_node.id][resource.name] = demand

        for node in system.nodes:
            solution.load_distribution[app.id][node.id][cloud_node.id] = 1.0

    return solution


def make_max_instances_constraint_feasible(system, solution, environment_input):
    """Satisfy the constraint of maximum number of instances

    Args:
        system (sp.core.model.system.System): system
        solution (sp.system_controller.model.opt_solution.OptSolution): optimization solution
        environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
    Returns:
        sp.system_controller.model.opt_solution.OptSolution: feasible solution
    """
    cloud_node = system.cloud_node
    for app in system.apps:
        instances = [n for n in system.nodes if solution.app_placement[app.id][n.id]]
        if len(instances) <= app.max_instances:
            continue

        if not solution.app_placement[app.id][cloud_node.id]:
            solution.app_placement[app.id][cloud_node.id] = True
            instances.append(cloud_node)

        instances.sort(key=lambda n: solution.received_load[app.id][n.id])
        while len(instances) > app.max_instances:
            dst_node = instances.pop()
            if dst_node == cloud_node:
                instances.insert(0, cloud_node)
                continue

            solution.app_placement[app.id][dst_node.id] = False
            solution.received_load[app.id][cloud_node.id] += solution.received_load[app.id][dst_node.id]
            solution.received_load[app.id][dst_node.id] = 0.0

            cloud_rl = solution.received_load[app.id][cloud_node.id]
            for resource in system.resources:
                demand = app.demand[resource.name](cloud_rl)
                solution.allocated_resource[app.id][cloud_node.id][resource.name] = demand
                solution.allocated_resource[app.id][dst_node.id][resource.name] = 0.0

            ld = solution.load_distribution
            for src_node in system.nodes:
                ld[app.id][src_node.id][cloud_node.id] += ld[app.id][src_node.id][dst_node.id]
                ld[app.id][src_node.id][dst_node.id] = 0.0

    return solution


def make_load_distribution_constraint_feasible(system, solution, environment_input):
    """Satisfy the constraint of load distribution

    Args:
        system (sp.core.model.system.System): system
        solution (sp.system_controller.model.opt_solution.OptSolution): optimization solution
        environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
    Returns:
        sp.system_controller.model.opt_solution.OptSolution: feasible solution
    """
    cloud_node = system.cloud_node
    for app in system.apps:
        instances = [n for n in system.nodes if solution.app_placement[app.id][n.id]]
        if len(instances) == 0:
            continue

        for src_node in system.nodes:
            src_ld = 0.0
            for dst_node in instances:
                src_ld += solution.load_distribution[app.id][src_node.id][dst_node.id]

            remaining_ld = 1.0 - src_ld
            remaining_ld = round(remaining_ld, ROUND_PRECISION)
            if remaining_ld > 0.0:
                dst_node = None
                if solution.app_placement[app.id][cloud_node.id]:
                    dst_node = cloud_node
                else:
                    instances.sort(key=lambda n: environment_input.get_net_delay(app.id, src_node.id, n.id))
                    dst_node = instances[0]

                total_load = calc_load_before_distribution(app.id, src_node.id, system, environment_input)
                remaining_load = remaining_ld * total_load
                solution.load_distribution[app.id][src_node.id][dst_node.id] += remaining_ld
                solution.received_load[app.id][dst_node.id] += remaining_load

                received_load = solution.received_load[app.id][dst_node.id]
                for resource in system.resources:
                    demand = app.demand[resource.name](received_load)
                    solution.allocated_resource[app.id][dst_node.id][resource.name] = demand

    return solution


def _round_values(system, solution, environment_input=None):
    """Round values of a solution

    Args:
        system (sp.core.model.system.System): system
        solution (sp.system_controller.model.opt_solution.OptSolution): optimization solution
        environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
    Returns:
        sp.system_controller.model.opt_solution.OptSolution: rounded solution
    """

    for app in system.apps:
        for dst_node in system.nodes:
            value = solution.received_load[app.id][dst_node.id]
            value = round(value, ROUND_PRECISION)
            solution.received_load[app.id][dst_node.id] = value

            for src_node in system.nodes:
                value = solution.load_distribution[app.id][src_node.id][dst_node.id]
                value = round(value, ROUND_PRECISION)
                solution.load_distribution[app.id][src_node.id][dst_node.id] = value

            for resource in system.resources:
                value = solution.allocated_resource[app.id][dst_node.id][resource.name]
                value = round(value, ROUND_PRECISION)
                solution.allocated_resource[app.id][dst_node.id][resource.name] = value

    return solution
