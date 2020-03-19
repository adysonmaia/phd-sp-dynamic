from sp.core.estimator import Estimator, abstractmethod
from sp.core.model import System
from sp.system_controller.estimator.processing import DefaultProcessingEstimator

INF = float("inf")


class SystemEstimator(Estimator):
    @abstractmethod
    def calc(self, system, control_input, environment_input):
        pass


class DefaultSystemEstimator(SystemEstimator):
    def calc(self, system, control_input, environment_input):
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
