from sp.system_controller.estimator.system import SystemEstimator
from sp.hierarchical_controller.cluster_ctrl.model import ClusterSystem, ClusterControlInput, ClusterEnvironmentInput
from sp.hierarchical_controller.cluster_ctrl.estimator.processing import ClusterProcessingEstimator


class ClusterSystemEstimator(SystemEstimator):
    """Cluster System Estimator
    """

    def calc(self, system, control_input, environment_input):
        """Estimate the next state of a system based on control and environment inputs

        Args:
            system (ClusterSystem): current system's state
            control_input (ClusterControlInput): control input
            environment_input (ClusterEnvironmentInput): environment input
        Returns:
            ClusterSystem: estimated next system's state
        """

        next_system = ClusterSystem()
        next_system.time = system.time + system.sampling_time
        next_system.sampling_time = system.sampling_time
        next_system.scenario = system.scenario
        next_system.real_scenario = system.real_scenario
        next_system.control_input = control_input
        next_system.environment_input = environment_input

        proc_estimator = ClusterProcessingEstimator()
        for app in next_system.apps:
            for dst_node in next_system.nodes:
                if not control_input.get_app_placement(app.id, dst_node.id):
                    continue

                proc_result = proc_estimator.calc(app.id, dst_node.id,
                                                  system=system,
                                                  control_input=control_input,
                                                  environment_input=environment_input)

                next_system.processing_delay[app.id][dst_node.id] = proc_result.delay
                next_system.app_queue_size[app.id][dst_node.id] = proc_result.queue_size

        return next_system
