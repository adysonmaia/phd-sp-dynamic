def make_solution_feasible(system, solution):
    solution = make_max_instances_constraint_feasible(system, solution)
    solution = make_load_distribution_constraint_feasible(system, solution)

    return solution


def make_max_instances_constraint_feasible(system, solution):
    cloud_node = system.cloud_node
    for app in system.apps:
        instances = []
        for dst_node in system.nodes:
            if solution.app_placement[app.id][dst_node.id]:
                instances.append(dst_node)

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


def make_load_distribution_constraint_feasible(system, solution):
    cloud_node = system.cloud_node
    for app in system.apps:
        instances = []
        for dst_node in system.nodes:
            if solution.app_placement[app.id][dst_node.id]:
                instances.append(dst_node)

        for src_node in system.nodes:
            ld = 0.0
            for dst_node in instances:
                ld += solution.load_distribution[app.id][src_node.id][dst_node.id]

            remaining_ld = 1.0 - ld
            if remaining_ld > 0.0:
                dst_node = None
                if solution.app_placement[app.id][cloud_node.id]:
                    dst_node = cloud_node
                else:
                    instances.sort(key=lambda n: system.get_net_delay(app.id, src_node.id, n.id))
                    dst_node = instances[0]

                remaining_load = remaining_ld * system.get_request_load(app.id, src_node.id)
                solution.load_distribution[app.id][src_node.id][dst_node.id] += remaining_ld
                solution.received_load[app.id][dst_node.id] += remaining_load

                if remaining_load > 0.0:
                    load = solution.received_load[app.id][dst_node.id]
                    for resource in system.resources:
                        demand = app.demand[resource.name](load)
                        solution.allocated_resource[app.id][dst_node.id][resource.name] = demand

    return solution
