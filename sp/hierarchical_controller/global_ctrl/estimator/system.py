from sp.system_controller.estimator.system import SystemEstimator
from sp.hierarchical_controller.global_ctrl.model import GlobalSystem, GlobalControlInput, GlobalEnvironmentInput
from sp.hierarchical_controller.global_ctrl.estimator.processing import GlobalProcessingEstimator


class GlobalSystemEstimator(SystemEstimator):
    """Global System Estimator
    """

    def calc(self, system, control_input, environment_input):
        """Estimate the next state of a system based on control and environment inputs

        Args:
            system (GlobalSystem): current system's state
            control_input (GlobalControlInput): control input
            environment_input (GlobalEnvironmentInput): environment input
        Returns:
            GlobalSystem: estimated next system's state
        """
        next_system = GlobalSystem()
        next_system.time = system.time + system.sampling_time
        next_system.sampling_time = system.sampling_time
        next_system.scenario = system.scenario
        next_system.real_scenario = system.real_scenario
        next_system.real_system = None
        next_system.control_input = control_input
        next_system.environment_input = environment_input

        proc_estimator = GlobalProcessingEstimator()
        for app in next_system.apps:
            for dst_node in next_system.nodes:
                if control_input.get_app_placement(app.id, dst_node.id) <= 0:
                    continue

                proc_result = proc_estimator.calc(app.id, dst_node.id,
                                                  system=system,
                                                  control_input=control_input,
                                                  environment_input=environment_input)

                next_system.processing_delay[app.id][dst_node.id] = proc_result.delay
                next_system.app_queue_size[app.id][dst_node.id] = proc_result.queue_size

        return next_system

