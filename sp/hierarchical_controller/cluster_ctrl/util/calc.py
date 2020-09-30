from sp.system_controller.util.calc import calc_network_delay, calc_initialization_delay
from sp.system_controller.util.calc import calc_app_size, calc_min_migration_delay
from sp.hierarchical_controller.global_ctrl.model import GlobalNode
from sp.hierarchical_controller.cluster_ctrl.model import ClusterSystem, ClusterControlInput, ClusterEnvironmentInput
import math


def calc_response_time(app_id, src_node_id, dst_node_id, system, control_input, environment_input):
    """Calculate average request response time

    Args:
        app_id (int): id of the requested application
        src_node_id (int): source node's id of the request
        dst_node_id (int): id of the node where the request is processed
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput): environment input
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
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput): environment input
    Returns:
        float: processing delay
    """
    from sp.hierarchical_controller.cluster_ctrl.estimator import ClusterProcessingEstimator
    proc_delay = math.inf

    alloc_cpu = control_input.get_allocated_cpu(app_id, node_id)
    if alloc_cpu > 0.0:
        proc_estimator = ClusterProcessingEstimator()
        proc_result = proc_estimator.calc(app_id, node_id, system, control_input, environment_input)
        proc_delay = proc_result.delay

    return proc_delay


def calc_load_before_distribution(app_id, node_id, system, environment_input):
    """Calculate load before distribution

    Args:
        app_id (int): application's id
        node_id (int): id of the node that is source of load
        system (ClusterSystem): system
        environment_input (ClusterEnvironmentInput): environment input
    Returns:
        float: load
    """
    node = system.get_node(node_id)
    load = environment_input.get_generated_load(app_id, node_id)
    if not isinstance(node, GlobalNode):
        load += system.get_app_queue_size(app_id, node_id) / float(system.sampling_time)
    return load


def calc_load_after_distribution(app_id, src_node_id, dst_node_id, system, control_input, environment_input,
                                 per_instance=True):
    """Calculate load after the distribution.
    It the amount of load from a source node distributed to a destination node

    Args:
        app_id (id): application's id
        src_node_id (int): source node's id
        dst_node_id (int): destination node's id
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput): environment input
        per_instance (bool): if it returns the load per instance
    Returns:
        float: load
    """
    ld = control_input.get_load_distribution(app_id, src_node_id, dst_node_id)
    load = calc_load_before_distribution(app_id, src_node_id, system, environment_input)
    dst_node = system.get_node(dst_node_id)
    if per_instance and isinstance(dst_node, GlobalNode):
        nb_instances = environment_input.get_nb_instances(app_id, dst_node_id)
        if nb_instances > 0:
            load = load / float(nb_instances)
        elif not control_input.get_app_placement(app_id, dst_node_id):
            load = 0.0
    return load * ld


def calc_received_load(app_id, node_id, system, control_input, environment_input, use_cache=True, per_instance=True):
    """Calculate the amount of load received by an application instance in a node

    Args:
        app_id (int): application's id
        node_id (int): node's id
        system (ClusterSystem): system
        control_input (ClusterControlInput): control input
        environment_input (ClusterEnvironmentInput): environment input
        use_cache (bool): use cached calculation
        per_instance (bool): if it returns the load per instance
    Returns:
        float: load
    """
    node = system.get_node(node_id)
    load = 0.0
    if use_cache:
        load = control_input.get_received_load(app_id, node_id)
        if not per_instance and isinstance(node, GlobalNode):
            nb_instances = environment_input.get_nb_instances(app_id, node_id)
            load *= nb_instances
    else:
        load = sum(map(lambda n: calc_load_after_distribution(app_id, n.id, node_id,
                                                              system, control_input, environment_input,
                                                              per_instance=True),
                       system.nodes))
        if isinstance(node, GlobalNode):
            load += environment_input.get_additional_received_load(app_id, node_id)
            if not per_instance:
                nb_instances = environment_input.get_nb_instances(app_id, node_id)
                if control_input.get_app_placement(app_id, node_id):
                    nb_instances = int(max(1, nb_instances))
                load *= nb_instances

    return load
