from sp.system_controller.model import OptSolution
import math


def calc_response_time(app_id, src_node_id, dst_node_id, system, control_input, environment_input):
    net_delay = calc_network_delay(app_id, src_node_id, dst_node_id, system, control_input, environment_input)
    proc_delay = calc_processing_delay(app_id, dst_node_id, system, control_input, environment_input)
    init_delay = calc_initialization_delay(app_id, dst_node_id, system, control_input, environment_input)
    return net_delay + proc_delay + init_delay


def calc_processing_delay(app_id, node_id, system, control_input, environment_input):
    from sp.system_controller.estimator.processing import DefaultProcessingEstimator, DefaultProcessingResult
    proc_delay = math.inf

    # TODO: make this calculation works with any ProcessingEstimator selected for the simulation
    alloc_cpu = control_input.get_allocated_cpu(app_id, node_id)
    if alloc_cpu > 0.0:
        proc_result = None
        if isinstance(control_input, OptSolution):
            app = system.get_app(app_id)
            arrival_rate = control_input.get_received_load(app_id, node_id)
            service_rate = alloc_cpu / float(app.work_size)
            proc_result = DefaultProcessingResult(arrival_rate, service_rate)
        else:
            proc_estimator = DefaultProcessingEstimator()
            proc_result = proc_estimator(app_id, node_id,
                                         system=system,
                                         control_input=control_input,
                                         environment_input=environment_input)
        proc_delay = proc_result.delay

    return proc_delay


def calc_network_delay(app_id, src_node_id, dst_node_id, system, control_input, environment_input):
    return environment_input.get_net_delay(app_id, src_node_id, dst_node_id)


def calc_initialization_delay(app_id, node_id, system, control_input, environment_input):
    # TODO: improve this estimation
    curr_control = system.control_input
    delay = 0.0
    # if curr_control is not None and not curr_control.get_app_placement(app_id, node_id):
    #     delay = 1.0
        # cloud_node = system.cloud_node
        # delay = environment_input.get_net_delay(app_id, cloud_node.id, node_id)

    return delay


def calc_load_before_distribution(app_id, node_id, system, environment_input):
    # TODO: create an estimator to do this calculation
    load = environment_input.get_generated_load(app_id, node_id)
    load += system.get_app_queue_size(app_id, node_id) / float(system.sampling_time)
    return load


