def make_max_instances_constraint_feasible(system, alloc):
    cloud_node = system.cloud_node
    for app in system.apps:
        instances = []
        for dst_node in system.nodes:
            if alloc.get_app_placement(app.id, dst_node.id):
                instances.append(dst_node)

        if len(instances) <= app.max_instances:
            continue

        if not alloc.get_app_placement(app.id, cloud_node.id):
            alloc.set_app_placement(app.id, cloud_node.id, True)
            instances.append(cloud_node)

        while len(instances) > app.max_instances:
            dst_node = instances.pop()
            if dst_node == cloud_node:
                instances.insert(0, cloud_node)
                continue

            alloc.set_app_placement(app.id, dst_node.id, False)
            for src_node in system.nodes:
                cloud_ld = alloc.get_load_distribution(app.id, cloud_node.id)
                ld = alloc.get_load_distribution(app.id, src_node.id, dst_node.id)
                cloud_ld += ld

                alloc.set_load_distribution(app.id, cloud_node.id, cloud_ld)
                alloc.set_load_distribution(app.id, dst_node.id, 0.0)

    return alloc


def make_load_distribution_constraint_feasible(system, alloc):
    cloud_node = system.cloud_node
    for app in system.apps:
        instances = []
        for dst_node in system.nodes:
            if alloc.get_app_placement(app.id, dst_node.id):
                instances.append(dst_node)

        for src_node in system.nodes:
            ld = 0.0
            for dst_node in instances:
                ld += alloc.get_load_distribution(app.id, src_node.id, dst_node.id)

            remaining_ld = 1.0 - ld
            if remaining_ld > 0.0:
                dst_node = None
                if alloc.get_app_placement(app.id, cloud_node.id):
                    dst_node = cloud_node
                else:
                    instances.sort(key=lambda n: system.get_net_delay(app.id, src_node.id, n.id))
                    dst_node = instances[0]

                dst_ld = alloc.get_load_distribution(app.id, dst_node.id)
                dst_ld += remaining_ld
                alloc.set_load_distribution(app.id, dst_node.id, dst_ld)

    return alloc


def local_search(system, alloc):
    alloc = make_max_instances_constraint_feasible(system, alloc)
    alloc = make_load_distribution_constraint_feasible(system, alloc)

    return alloc


def is_valid(system, alloc=None):
    if alloc is None:
        alloc = system.allocation

    for app in system.apps:
        nb_instances = sum(list(filter(lambda n: alloc.get_app_placement(app.id, n.id), system.nodes)))
        if nb_instances > app.max_instances or nb_instances == 0:
            return False
        for src_node in system.nodes:
            ld = 0.0
            for dst_node in system.nodes:
                dst_ld = alloc.get_load_distribution(app.id, src_node.id, dst_node.id)
                if dst_ld > 0.0 and not alloc.get_app_placement(app.id, dst_node.id):
                    return False
                ld += dst_ld

    for dst_node in system.nodes:
        for resource in system.resources:
            demand = 0.0
            for app in system.apps:
                dst_load = 0.0
                for src_node in system.nodes:
                    ld = alloc.get_load_distribution(app.id, src_node.id, dst_node.id)
                    src_load = system.get_request_load(app.id, src_node.id)
                    dst_load += float(ld * src_load)
                if dst_load > 0.0:
                    if not alloc.get_app_placement(app.id, dst_node.id):
                        return False
                    demand += app.demand[resource.name](dst_load)
            if demand > dst_node.capacity[resource.name]:
                return False

    return True

