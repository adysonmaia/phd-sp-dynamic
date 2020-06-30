from sp.core.model import Resource, System, ControlInput, EnvironmentInput
from sp.system_controller.model import OptSolution
import math


def calc_response_time(app_id, src_node_id, dst_node_id, system, control_input, environment_input):
    """Calculate average request response time

    Args:
        app_id (int): id of the requested application
        src_node_id (int): source node's id of the request
        dst_node_id (int): id of the node where the request is processed
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput): environment input
    Returns:
        float: response time
    """
    net_delay = calc_network_delay(app_id, src_node_id, dst_node_id, system, control_input, environment_input)
    proc_delay = calc_processing_delay(app_id, dst_node_id, system, control_input, environment_input)
    init_delay = calc_initialization_delay(app_id, dst_node_id, system, control_input, environment_input)

    return net_delay + proc_delay + init_delay


def calc_processing_delay(app_id, node_id, system, control_input, environment_input):
    """Calculate the average request processing delay

    Args:
        app_id (int): id of the requested application
        node_id (int): id of the node where the request is processed
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput): environment input
    Returns:
        float: processing delay
    """
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
    """Calculate average request network delay

    Args:
        app_id (int): id of the requested application
        src_node_id (int): source node's id of the request
        dst_node_id (int): id of the node where the request is processed
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput): environment input
    Returns:
        float: network delay
    """
    return environment_input.get_net_delay(app_id, src_node_id, dst_node_id)


def calc_initialization_delay(app_id, node_id, system, control_input, environment_input):
    """Calculate initialization delay of application instance in a node

    Args:
        app_id (int): application's id
        node_id (int): node's id
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput): environment input
    Returns:
        float: initialization delay
    """
    curr_control = system.control_input
    next_control = control_input
    init = (curr_control is not None
            and not curr_control.get_app_placement(app_id, node_id)
            and next_control.get_app_placement(app_id, node_id))

    if not init:
        return 0.0

    # TODO: create a estimator to calculate this delay
    init_delay = 0.0
    t = system.sampling_time
    mig_delay = calc_migration_delay(app_id, node_id, system, control_input, environment_input)
    if t > mig_delay:
        # mig_delay = math.ceil(mig_delay)
        # t = math.ceil(t)
        init_delay = mig_delay * (mig_delay + 1.0) / (2.0 * t)
    else:
        init_delay = mig_delay

    # init_delay = 0.0
    # mig_delay = math.ceil(calc_migration_delay(app_id, node_id, system, control_input, environment_input))
    # if mig_delay > 0.0 and system.sampling_time > 0.0:
    #     init_delay = (mig_delay ** 2) / float(system.sampling_time)

    return init_delay


def calc_migration_size(app_id, dst_node_id, system, control_input, environment_input, return_extra_data=False):
    """Calculate the application size that will be migrated/replicated to a destination node

    Args:
        app_id (int): application's id
        dst_node_id (int): destination node's id
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput): environment input
        return_extra_data (bool): whether additional information should be return or not.
            This include source node's id, which is a node hosting the selected application instance
            that will be migrated/replicated to the destination node
    Returns:
        Union[float, tuple]: application's size or tuple (app size, src node id)
    """
    curr_control = system.control_input
    if curr_control is None:
        return (0.0, None) if return_extra_data else 0.0

    min_delay = math.inf
    src_node_id = system.cloud_node.id
    for node in system.nodes:
        if not curr_control.get_app_placement(app_id, node.id):
            continue
        delay = environment_input.get_net_delay(app_id, node.id, dst_node_id)
        if delay < min_delay:
            min_delay = delay
            src_node_id = node.id

    app_size = 0.0
    for resource_name in [Resource.RAM, Resource.DISK]:
        if resource_name in system.resources_name:
            app_size += curr_control.get_allocated_resource(app_id, src_node_id, resource_name)
    # TODO: Transform storage unit to bandwidth unit in general form
    app_size *= 8.0  # Convert byte to bit
    return (app_size, src_node_id) if return_extra_data else app_size


def calc_migration_delay(app_id, dst_node_id, system, control_input, environment_input, return_extra_data=False):
    """Calculate migration/replication delay of an application that will be hosted in a destination node

    Args:
        app_id (int): application's id
        dst_node_id (int): destination node's id
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput): environment input
        return_extra_data (bool): whether additional information should be return or not.
            This include application's size and source node's id.
            A source node is a node hosting the selected application instance that will be migrated/replicated
            to the destination node
    Returns:
        Union[float, tuple]: migration delay or tuple (mig delay, app size, src node id)
    """
    curr_control = system.control_input
    if curr_control is None:
        return (0.0, 0.0, None) if return_extra_data else 0.0

    app_size, src_node_id = calc_migration_size(app_id, dst_node_id, system, control_input, environment_input,
                                                return_extra_data=True)
    # TODO: create a estimator to calculate the migration time
    mig_delay = 0.0
    if app_size > 0.0:
        net_path = environment_input.get_net_path(app_id, src_node_id, dst_node_id)
        if len(net_path) > 0:
            link_src_id = net_path[0]
            for link_dst_id in net_path[1:]:
                link = system.get_link(link_src_id, link_dst_id)
                delay = link.propagation_delay + app_size / float(link.bandwidth)
                mig_delay += delay
                link_src_id = link_dst_id

    return (mig_delay, app_size, src_node_id) if return_extra_data else mig_delay


def calc_load_before_distribution(app_id, node_id, system, environment_input):
    """Calculate load before distribution

    Args:
        app_id (int): application's id
        node_id (int): id of the node that is source of load
        system (System): system
        environment_input (EnvironmentInput): environment input
    Returns:
        float: load
    """
    load = environment_input.get_generated_load(app_id, node_id)
    load += system.get_app_queue_size(app_id, node_id) / float(system.sampling_time)
    return load


def calc_load_after_distribution(app_id, src_node_id, dst_node_id, system, control_input, environment_input):
    """Calculate load after the distribution.
    It the amount of load from a source node distributed to a destination node

    Args:
        app_id (id): application's id
        src_node_id (int): source node's id
        dst_node_id (int): destination node's id
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput): environment input
    Returns:
        float: load
    """
    ld = control_input.get_load_distribution(app_id, src_node_id, dst_node_id)
    load = calc_load_before_distribution(app_id, src_node_id, system, environment_input)
    return load * ld


def calc_received_load(app_id, node_id, system, control_input, environment_input, use_cache=True):
    """Calculate the amount of load received by a node for an application

    Args:
        app_id (int): application's id
        node_id (int): node's id
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput): environment input
        use_cache (bool): use cached calculation
    Returns:
        float: load
    """
    load = 0.0
    if isinstance(control_input, OptSolution) and use_cache:
        load = control_input.get_received_load(app_id, node_id)
    else:
        load = sum(map(lambda src_node: calc_load_after_distribution(app_id, src_node.id, node_id,
                                                                     system, control_input, environment_input),
                       system.nodes))
    return load
