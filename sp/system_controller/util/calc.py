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
        proc_result = proc_estimator.calc(app_id, node_id, system, control_input, environment_input)
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
    mig_delay = calc_min_migration_delay(app_id, node_id, system, control_input, environment_input)
    if t > mig_delay:
        # mig_delay = math.ceil(mig_delay)
        # t = math.ceil(t)
        init_delay = mig_delay * (mig_delay + 1.0) / (2.0 * t)
    else:
        init_delay = mig_delay

    # init_delay = 0.0
    # mig_delay = math.ceil(calc_min_migration_delay(app_id, node_id, system, control_input, environment_input))
    # if mig_delay > 0.0 and system.sampling_time > 0.0:
    #     init_delay = (mig_delay ** 2) / float(system.sampling_time)

    return init_delay


def calc_app_size(app_id, node_id, system, control_input, environment_input, ignore_placement=False):
    """Calculate the size of an application placed on a node.
    The size comprises the amount of DISK plus RAM allocated to this application

    Args:
        app_id (int): application's id
        node_id (int): node's id
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput): environment input
        ignore_placement (bool): whether the placement decision should be ignored or not.
            If True and application is not placed on the specified node,
            the size of an application is calculated using its demand estimator with zero demand as argument.
    Returns:
        float: application's size
    """
    app_size = 0.0
    resources_name = list(filter(lambda r: r in system.resources_name, [Resource.RAM, Resource.DISK]))

    if control_input is not None and control_input.get_app_placement(app_id, node_id):
        for resource_name in resources_name:
            app_size += control_input.get_allocated_resource(app_id, node_id, resource_name)
    elif ignore_placement:
        app = system.get_app(app_id)
        load = 0.0
        for resource_name in resources_name:
            app_size += app.demand[resource_name](load)

    return app_size


def calc_migration_delay(app_id, src_node_id, dst_node_id, system, control_input, environment_input,
                         ignore_placement=False):
    """Calculate the delay to migrate/replicate an application from a source node to a destination node.

    Args:
        app_id (int): application's id
        src_node_id (int): source node's id
        dst_node_id (int): destination node's id
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput): environment input
        ignore_placement (bool): whether the current placement should be ignored or not.
    Returns:
        float: migration delay. It returns infinity if the source node isn't hosting the application
    """
    if system.control_input is None and not ignore_placement:
        return 0.0

    app_size = calc_app_size(app_id, src_node_id, system, system.control_input, environment_input,
                             ignore_placement=ignore_placement)
    if app_size == 0.0:
        return math.inf

    # TODO: put this net delay calculation in an Estimator
    mig_delay = 0.0
    net_path = environment_input.get_net_path(app_id, src_node_id, dst_node_id)
    if len(net_path) > 0:
        app_size_bits = app_size * 8.0  # TODO: generalize this type conversion
        link_start_node_id = net_path[0]
        for link_end_node_id in net_path[1:]:
            link = system.get_link(link_start_node_id, link_end_node_id)
            delay = link.propagation_delay + (app_size_bits / float(link.bandwidth))
            mig_delay += delay
            link_start_node_id = link_end_node_id
    elif src_node_id != dst_node_id:
        mig_delay = math.inf
    return mig_delay


def calc_min_migration_delay(app_id, dst_node_id, system, control_input, environment_input, return_src_node_id=False):
    """Calculate minimum migration/replication delay of an application that will be hosted in a destination node

    Args:
        app_id (int): application's id
        dst_node_id (int): destination node's id
        system (System): system
        control_input (ControlInput): control input
        environment_input (EnvironmentInput): environment input
        return_src_node_id (bool): whether source node's id should be return or not.
            A source node is a node hosting the selected application instance that will be migrated/replicated
            to the destination node
    Returns:
        Union[float, tuple]: migration delay or tuple (mig delay, src node id)
    """
    curr_control = system.control_input
    if curr_control is None or curr_control.get_app_placement(app_id, dst_node_id):
        return (0.0, dst_node_id) if return_src_node_id else 0.0

    min_delay = math.inf
    selected_src_node_id = None
    for src_node in system.nodes:
        if not curr_control.get_app_placement(app_id, src_node.id) or src_node.id == dst_node_id:
            continue
        delay = calc_migration_delay(app_id, src_node.id, dst_node_id, system, control_input, environment_input)
        # delay = environment_input.get_net_delay(app_id, src_node.id, dst_node_id)
        if delay < min_delay:
            min_delay = delay
            selected_src_node_id = src_node.id

    mig_delay = None
    if selected_src_node_id is None:
        selected_src_node_id = system.cloud_node.id
        mig_delay = calc_migration_delay(app_id, selected_src_node_id, dst_node_id,
                                         system, control_input, environment_input, ignore_placement=True)
    else:
        mig_delay = min_delay
        # mig_delay = calc_migration_delay(app_id, selected_src_node_id, dst_node_id,
        #                                  system, control_input, environment_input)

    return (mig_delay, selected_src_node_id) if return_src_node_id else mig_delay


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
