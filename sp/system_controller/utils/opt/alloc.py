def alloc_demanded_resources(system, solution):
    for app in system.apps:
        for dst_node in system.nodes:
            if solution.app_placement[app.id][dst_node.id]:
                dst_load = 0.0
                for src_node in system.nodes:
                    ld = solution.load_distribution[app.id][src_node.id][dst_node.id]
                    src_load = system.get_request_load(app.id, src_node.id)
                    dst_load += float(ld * src_load)
                solution.received_load[app.id][dst_node.id] = dst_load
                for resource in system.resources:
                    demand = app.demand[resource.name](dst_load)
                    solution.allocated_resource[app.id][dst_node.id][resource.name] = demand
            else:
                solution.received_load[app.id][dst_node.id] = 0.0
                for src_node in system.nodes:
                    solution.load_distribution[app.id][src_node.id][dst_node.id] = 0.0
                for resource in system.resources:
                    solution.allocated_resource[app.id][dst_node.id][resource.name] = 0.0
    return solution
