from sp.core.estimator import Estimator
from sp.core.model import System, ControlInput, EnvironmentInput
from sp.system_controller.estimator.processing import DefaultProcessingEstimator
from abc import abstractmethod


class SystemEstimator(Estimator):
    """System State Estimator Abstract Class
    """

    @abstractmethod
    def calc(self, system, control_input, environment_input):
        """Estimate the next state of a system based on control and environment inputs

        Args:
            system (System): current system's state
            control_input (ControlInput): control input
            environment_input (EnvironmentInput): environment input
        Returns:
            System: estimated next system's state
        """
        pass


class DefaultSystemEstimator(SystemEstimator):
    """Default System State Estimator
    """

    def calc(self, system, control_input, environment_input):
        """Estimate the next state of a system based on control and environment inputs

        Args:
            system (System): current system's state
            control_input (ControlInput): control input
            environment_input (EnvironmentInput): environment input
        Returns:
            System: estimated next system's state
        """
        next_system = System()
        next_system.time = system.time + system.sampling_time
        next_system.sampling_time = system.sampling_time
        next_system.scenario = system.scenario
        next_system.control_input = control_input
        next_system.environment_input = environment_input

        proc_estimator = DefaultProcessingEstimator()
        for app in next_system.apps:
            for dst_node in next_system.nodes:
                if not control_input.get_app_placement(app.id, dst_node.id):
                    continue

                proc_result = proc_estimator(app.id, dst_node.id,
                                             system=system,
                                             control_input=control_input,
                                             environment_input=environment_input)

                next_system.processing_delay[app.id][dst_node.id] = proc_result.delay
                next_system.app_queue_size[app.id][dst_node.id] = proc_result.queue_size

        return next_system
