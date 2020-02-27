from sp.core.model import Resource

INF = float("inf")


def calc_response_time(app, src_node, dst_node, system, solution):
    net_delay = calc_network_delay(app, src_node, dst_node, system, solution)
    proc_delay = calc_processing_delay(app, dst_node, system, solution)
    return net_delay + proc_delay


def calc_processing_delay(app, node, system, solution):
    proc_delay = INF

    if solution.app_placement[app.id][node.id]:
        alloc_cpu = solution.allocated_resource[app.id][node.id][Resource.CPU]
        arrival_rate = solution.received_load[node.id][app.id]
        service_rate = alloc_cpu / float(app.work_size)

        if service_rate > arrival_rate:
            proc_delay = 1.0 / float(service_rate - arrival_rate)

    return proc_delay


def calc_network_delay(app, src_node, dst_node, system, solution):
    return system.get_net_delay(app.id, src_node.id, dst_node.id)

