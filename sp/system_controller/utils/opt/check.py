ERROR_TOLERANCE = 0.0001


def is_solution_valid(system, solution):
    for app in system.apps:
        nb_instances = sum([solution.app_placement[app.id][n.id] for n in system.nodes])
        if nb_instances > app.max_instances or nb_instances == 0:
            return False

        for src_node in system.nodes:
            src_ld = 0.0
            for dst_node in system.nodes:
                dst_ld = solution.load_distribution[app.id][src_node.id][dst_node.id]
                if dst_ld > 0.0 and not solution.app_placement[app.id][dst_node.id]:
                    return False

                src_ld += dst_ld
            if abs(1.0 - src_ld) > ERROR_TOLERANCE:
                return False

    for dst_node in system.nodes:
        for resource in system.resources:
            allocated = 0.0
            for app in system.apps:
                dst_load = 0.0
                for src_node in system.nodes:
                    ld = solution.load_distribution[app.id][src_node.id][dst_node.id]
                    src_load = system.get_request_load(app.id, src_node.id)
                    dst_load += float(ld * src_load)

                received_load = solution.received_load[app.id][dst_node.id]
                if abs(dst_load - received_load) > ERROR_TOLERANCE:
                    return False

                if dst_load > 0.0:
                    if not solution.app_placement[app.id][dst_node.id]:
                        return False

                    app_demand = app.demand[resource.name](dst_load)
                    alloc_res = solution.allocated_resource[app.id][dst_node.id][resource.name]
                    if abs(app_demand - alloc_res) > ERROR_TOLERANCE:
                        return False

                    allocated += app_demand
            if allocated > dst_node.capacity[resource.name]:
                return False

    return True
