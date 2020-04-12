from sp.system_controller.utils.calc import calc_received_load


def alloc_demanded_resources(system, solution, environment_input):
    for app in system.apps:
        for dst_node in system.nodes:
            if solution.app_placement[app.id][dst_node.id]:
                dst_load = calc_received_load(app.id, dst_node.id, system, solution, environment_input,
                                              use_cache=False)
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
