from sp.core.model import Resource
from sp.system_controller.util.calc import calc_load_before_distribution, calc_network_delay, calc_app_size
from sp.hierarchical_controller.global_ctrl.model import GlobalSystem, GlobalControlInput, GlobalEnvironmentInput
import math


def calc_response_time(app_id, src_node_id, dst_node_id, system, control_input, environment_input):
    """Calculate average request response time

    Args:
        app_id (int): id of the requested application
        src_node_id (int): source node's id of the request
        dst_node_id (int): id of the node where the request is processed
        system (GlobalSystem): system
        control_input (GlobalControlInput): control input
        environment_input (GlobalEnvironmentInput): environment input
    Returns:
        float: response time
    """
    net_delay = calc_network_delay(app_id, src_node_id, dst_node_id, system, control_input, environment_input)
    proc_delay = calc_processing_delay(app_id, dst_node_id, system, control_input, environment_input)
    init_delay = calc_initialization_delay(app_id, dst_node_id, system, control_input, environment_input)

    return net_delay + proc_delay + init_delay


def calc_processing_delay(app_id, node_id, system, control_input, environment_input, use_cache=True):
    """Calculate the average request processing delay

    Args:
        app_id (int): id of the requested application
        node_id (int): id of the node where the request is processed
        system (GlobalSystem): system
        control_input (GlobalControlInput): control input
        environment_input (GlobalEnvironmentInput): environment input
        use_cache (bool): use cached calculation
    Returns:
        float: processing delay
    """
    from sp.hierarchical_controller.global_ctrl.estimator import GlobalProcessingEstimator
    proc_delay = math.inf

    alloc_cpu = control_input.get_allocated_cpu(app_id, node_id)
    if alloc_cpu > 0.0:
        proc_estimator = GlobalProcessingEstimator()
        proc_result = proc_estimator.calc(app_id, node_id, system, control_input, environment_input,
                                          use_cache=use_cache)
        proc_delay = proc_result.delay

    return proc_delay


def calc_initialization_delay(app_id, node_id, system, control_input, environment_input):
    """Calculate initialization delay of application instance in a node

    Args:
        app_id (int): application's id
        node_id (int): node's id
        system (GlobalSystem): system
        control_input (GlobalControlInput): control input
        environment_input (GlobalEnvironmentInput): environment input
    Returns:
        float: initialization delay
    """

    curr_control = system.control_input
    next_control = control_input
    if curr_control is None:
        return 0.0

    curr_place = curr_control.get_app_placement(app_id, node_id)
    next_place = next_control.get_app_placement(app_id, node_id)
    if next_place - curr_place <= 0:
        return 0.0

    init_delay = 0.0
    t = system.sampling_time
    mig_delay = calc_min_migration_delay(app_id, node_id, system, control_input, environment_input)
    if t > mig_delay:
        init_delay = mig_delay * (mig_delay + 1.0) / (2.0 * t)
    else:
        init_delay = mig_delay

    mig_delay = mig_delay * (1.0 - curr_place / float(next_place))
    return mig_delay


def calc_min_migration_delay(app_id, dst_node_id, system, control_input, environment_input, return_src_node_id=False):
    """Calculate minimum migration/replication delay of an application that will be hosted in a destination node

    Args:
        app_id (int): application's id
        dst_node_id (int): destination node's id
        system (GlobalSystem): system
        control_input (GlobalControlInput): control input
        environment_input (GlobalEnvironmentInput): environment input
        return_src_node_id (bool): whether source node's id should be return or not.
            A source node is a node hosting the selected application instance that will be migrated/replicated
            to the destination node
    Returns:
        Union[float, tuple]: migration delay or tuple (mig delay, src node id)
    """
    curr_control = system.control_input
    if curr_control is None:
        return (0.0, dst_node_id) if return_src_node_id else 0.0

    min_delay = math.inf
    selected_src_node_id = None
    for src_node in system.nodes:
        if curr_control.get_app_placement(app_id, src_node.id) <= 0:
            continue
        delay = calc_migration_delay(app_id, src_node.id, dst_node_id, system, control_input, environment_input)
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

    return (mig_delay, selected_src_node_id) if return_src_node_id else mig_delay


def calc_migration_delay(app_id, src_node_id, dst_node_id, system, control_input, environment_input,
                         ignore_placement=False):
    """Calculate the delay to migrate/replicate an application from a source node to a destination node.

    Args:
        app_id (int): application's id
        src_node_id (int): source node's id
        dst_node_id (int): destination node's id
        system (GlobalSystem): system
        control_input (GlobalControlInput): control input
        environment_input (GlobalEnvironmentInput): environment input
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

    mig_delay = 0.0
    real_net = system.real_scenario.network
    real_env = environment_input.real_environment_input
    src_node = system.get_node(src_node_id)
    dst_node = system.get_node(dst_node_id)

    if src_node_id == dst_node_id:
        central_node = dst_node.central_node
        real_nodes = dst_node.nodes

        for real_node in real_nodes:
            net_path = real_env.get_net_path(app_id, central_node.id, real_node.id)
            mig_delay += calc_transfer_time(app_size, net_path, real_net)
        if len(real_nodes) > 1:
            mig_delay = mig_delay / float(len(real_nodes) - 1)
    else:
        src_central_id = src_node.central_node_id
        dst_central_id = dst_node.central_node_id

        net_path = real_env.get_net_path(app_id, src_central_id, dst_central_id)
        mig_delay = calc_transfer_time(app_size, net_path, real_net)

    return mig_delay


def calc_transfer_time(data_size, path, graph):
    """Calculate data transfer time through the network

    Args:
        data_size (float): data size
        path (list): network path
        graph: network graph

    Returns:
        float: transfer time
    """
    t = 0.0
    if len(path) > 0:
        link_src = path[0]
        for link_dst in path[1:]:
            link = graph.get_link(link_src, link_dst)
            t += link.propagation_delay + (data_size / float(link.bandwidth))
            link_src = link_dst
    return t


def calc_load_after_distribution(app_id, src_node_id, dst_node_id, system, control_input, environment_input,
                                 per_instance=True):
    """Calculate load after the distribution.
    It the amount of load from a source node distributed to a destination node

    Args:
        app_id (id): application's id
        src_node_id (int): source node's id
        dst_node_id (int): destination node's id
        system (GlobalSystem): system
        control_input (GlobalControlInput): control input
        environment_input (GlobalEnvironmentInput): environment input
        per_instance (bool): if it returns the load per instance
    Returns:
        float: load
    """
    ld = control_input.get_load_distribution(app_id, src_node_id, dst_node_id)
    load = calc_load_before_distribution(app_id, src_node_id, system, environment_input)
    if per_instance:
        nb_instances = control_input.get_app_placement(app_id, dst_node_id)
        if nb_instances > 0:
            load = load / float(nb_instances)
        else:
            load = 0.0
    return load * ld


def calc_received_load(app_id, node_id, system, control_input, environment_input,
                       use_cache=True, per_instance=True):
    """Calculate the amount of load received by an application instance in a global node

    Args:
        app_id (int): application's id
        node_id (int): node's id
        system (GlobalSystem): system
        control_input (GlobalControlInput): control input
        environment_input (GlobalEnvironmentInput): environment input
        use_cache (bool): use cached calculation
        per_instance (bool): if it returns the load per instance
    Returns:
        float: load
    """
    load = 0.0
    nb_instances = control_input.get_app_placement(app_id, node_id)
    if use_cache:
        load = control_input.get_received_load(app_id, node_id)
        if not per_instance:
            load = load * nb_instances
    else:
        load = sum(map(lambda n: calc_load_after_distribution(app_id, n.id, node_id,
                                                              system, control_input, environment_input,
                                                              per_instance=False),
                       system.nodes))
        if per_instance:
            if nb_instances > 0:
                load = load / float(nb_instances)
            else:
                load = 0.0
    return load
