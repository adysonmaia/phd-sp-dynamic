from sp.system_controller.estimator.processing import ProcessingEstimator, DefaultProcessingResult
from sp.hierarchical_controller.cluster_ctrl.model import ClusterSystem, ClusterControlInput, ClusterEnvironmentInput
from sp.hierarchical_controller.cluster_ctrl.util.calc import calc_received_load


class ClusterProcessingResult(DefaultProcessingResult):
    """Global Processing Result
    """
    pass


class ClusterProcessingEstimator(ProcessingEstimator):
    """Global Processing Estimator
    """

    def calc(self, app_id, node_id, system, control_input, environment_input, use_cache=True):
        """Estimate the state of the processor

        Args:
            app_id (int): application's id
            node_id (int): node's id
            system (ClusterSystem): system
            control_input (ClusterControlInput): control input
            environment_input (ClusterEnvironmentInput):  environment input
            use_cache (bool): use cached calculation
        Returns:
            ClusterProcessingResult: processor's state
        """
        app = system.get_app(app_id)
        dst_node = system.get_node(node_id)

        arrival_rate = calc_received_load(app_id, node_id, system, control_input, environment_input,
                                          use_cache=use_cache, per_instance=True)
        alloc_cpu = control_input.get_allocated_cpu(app.id, dst_node.id)
        service_rate = alloc_cpu / float(app.work_size)

        return ClusterProcessingResult(arrival_rate, service_rate)
