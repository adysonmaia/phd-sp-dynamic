from sp.core.model import Resource
from sp.system_controller.model import OptSolution
import math


def calc_response_time(app_id, src_node_id, dst_node_id, system, control_input, environment_input):
    net_delay = calc_network_delay(app_id, src_node_id, dst_node_id, system, control_input, environment_input)
    proc_delay = calc_processing_delay(app_id, dst_node_id, system, control_input, environment_input)
    init_delay = calc_initialization_delay(app_id, dst_node_id, system, control_input, environment_input)

    rt = net_delay + proc_delay
    if init_delay > 0.0 and system.sampling_time > 0.0:
        rt += (init_delay ** 2) / float(system.sampling_time)
    return rt


def calc_processing_delay(app_id, node_id, system, control_input, environment_input):
    from sp.system_controller.estimator.processing import DefaultProcessingEstimator
    proc_delay = math.inf

    # TODO: make this calculation works with any ProcessingEstimator selected for the simulation
    alloc_cpu = control_input.get_allocated_cpu(app_id, node_id)
    if alloc_cpu > 0.0:
        proc_estimator = DefaultProcessingEstimator()
        proc_result = proc_estimator(app_id, node_id, system, control_input, environment_input)
        proc_delay = proc_result.delay

    return proc_delay


def calc_network_delay(app_id, src_node_id, dst_node_id, system, control_input, environment_input):
    return environment_input.get_net_delay(app_id, src_node_id, dst_node_id)


def calc_initialization_delay(app_id, node_id, system, control_input, environment_input):
    curr_control = system.control_input
    next_control = control_input
    init = (curr_control is not None
            and not curr_control.get_app_placement(app_id, node_id)
            and next_control.get_app_placement(app_id, node_id))

    init_delay = 0.0
    if not init:
        return init_delay

    selected_node = system.cloud_node
    min_delay = math.inf
    for src_node in system.nodes:
        if not curr_control.get_app_placement(app_id, src_node.id):
            continue

        delay = environment_input.get_net_delay(app_id, src_node.id, node_id)
        if delay < min_delay:
            min_delay = delay
            selected_node = src_node

    app_size = 0.0
    for resource_name in [Resource.RAM, Resource.DISK]:
        if resource_name in system.resources_name:
            app_size += curr_control.get_allocated_resource(app_id, selected_node.id, resource_name)
    # TODO: Transform storage unit to bandwidth unit in general form
    app_size *= 8.0

    # TODO: create a estimator to calculate the migration time
    net_path = environment_input.get_net_path(app_id, selected_node.id, node_id)
    if len(net_path) > 0 and app_size > 0.0:
        link_src_id = net_path[0]
        for link_dst_id in net_path[1:]:
            link = system.get_link(link_src_id, link_dst_id)
            delay = link.propagation_delay + app_size / float(link.bandwidth)
            init_delay += delay
            link_src_id = link_dst_id

    return init_delay


def calc_load_before_distribution(app_id, node_id, system, environment_input):
    load = environment_input.get_generated_load(app_id, node_id)
    load += system.get_app_queue_size(app_id, node_id) / float(system.sampling_time)
    return load


def calc_load_after_distribution(app_id, src_node_id, dst_node_id, system, control_input, environment_input):
    ld = control_input.get_load_distribution(app_id, src_node_id, dst_node_id)
    load = calc_load_before_distribution(app_id, src_node_id, system, environment_input)
    return load * ld


def calc_received_load(app_id, node_id, system, control_input, environment_input, use_cache=True):
    load = 0.0
    if isinstance(control_input, OptSolution) and use_cache:
        load = control_input.get_received_load(app_id, node_id)
    else:
        load = sum(map(lambda src_node: calc_load_after_distribution(app_id, src_node.id, node_id,
                                                                     system, control_input, environment_input),
                       system.nodes))
    return load
