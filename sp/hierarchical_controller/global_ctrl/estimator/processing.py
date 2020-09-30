from sp.system_controller.estimator.processing import ProcessingEstimator, DefaultProcessingResult
from sp.hierarchical_controller.global_ctrl.model import GlobalSystem, GlobalControlInput, GlobalEnvironmentInput
from sp.hierarchical_controller.global_ctrl.util.calc import calc_received_load


class GlobalProcessingResult(DefaultProcessingResult):
    """Global Processing Result
    """
    pass


class GlobalProcessingEstimator(ProcessingEstimator):
    """Global Processing Estimator
    """

    def calc(self, app_id, node_id, system, control_input, environment_input, use_cache=True):
        """Estimate the state of the processor

        Args:
            app_id (int): application's id
            node_id (int): node's id
            system (GlobalSystem): system
            control_input (GlobalControlInput): control input
            environment_input (GlobalEnvironmentInput):  environment input
            use_cache (bool): use cached calculation
        Returns:
            GlobalProcessingResult: processor's state
        """
        app = system.get_app(app_id)
        dst_node = system.get_node(node_id)

        arrival_rate = calc_received_load(app_id, node_id, system, control_input, environment_input,
                                          use_cache=use_cache, per_instance=True)
        alloc_cpu = control_input.get_allocated_cpu(app.id, dst_node.id)
        service_rate = alloc_cpu / float(app.work_size)

        return GlobalProcessingResult(arrival_rate, service_rate)
