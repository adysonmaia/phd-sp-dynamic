def alloc_demanded_resources(system, allocation):
    for app in system.apps:
        for dst_node in system.nodes:
            if allocation.get_app_placement(app.id, dst_node.id):
                dst_load = 0.0
                for src_node in system.nodes:
                    ld = allocation.get_load_distribution(app.id, src_node.id, dst_node.id)
                    src_load = system.get_request_load(app.id, src_node.id)
                    dst_load += float(ld * src_load)
                for resource in system.resources:
                    demand = app.get_demand(resource.name).calc(dst_load)
                    allocation.set_allocated_resource(app.id, dst_node.id, resource.name, demand)
            else:
                for resource in system.resources:
                    allocation.set_allocated_resource(app.id, dst_node.id, resource.name, 0.0)
