from sp.core.model import Resource
from sp.system_controller.model import OptSolution
import math


def calc_response_time(app_id, src_node_id, dst_node_id, system, control_input, environment_input):
    net_delay = calc_network_delay(app_id, src_node_id, dst_node_id, system, control_input, environment_input)
    proc_delay = calc_processing_delay(app_id, dst_node_id, system, control_input, environment_input)
    return net_delay + proc_delay


def calc_processing_delay(app_id, node_id, system, control_input, environment_input):
    from sp.system_controller.estimator.processing import DefaultProcessingEstimator, DefaultProcessingResult
    proc_delay = math.inf

    # TODO: make this calculation works with any ProcessingEstimator selected for the simulation
    if control_input.app_placement[app_id][node_id]:
        proc_result = None
        if isinstance(control_input, OptSolution):
            app = system.get_app(app_id)
            alloc_cpu = control_input.allocated_resource[app_id][node_id][Resource.CPU]
            arrival_rate = control_input.received_load[app_id][node_id]
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


def calc_load_before_distribution(app_id, node_id, system, environment_input):
    # TODO: create an estimator to do this calculation
    load = environment_input.get_generated_load(app_id, node_id)
    load += system.get_app_queue_size(app_id, node_id) / float(system.sampling_time)
    return load


