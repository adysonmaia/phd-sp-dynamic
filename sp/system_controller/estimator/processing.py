from sp.core.estimator import Estimator
from sp.system_controller.utils.calc import calc_received_load
from abc import ABC, abstractmethod
import math


class ProcessingEstimator(Estimator):
    @abstractmethod
    def calc(self, app_id, node_id, system, control_input, environment_input):
        pass


class ProcessingResult(ABC):
    def __init__(self, arrival_rate, service_rate):
        ABC.__init__(self)
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate

    @property
    @abstractmethod
    def delay(self):
        pass

    @property
    @abstractmethod
    def queue_size(self):
        pass


class DefaultProcessingEstimator(ProcessingEstimator):
    def calc(self, app_id, node_id, system, control_input, environment_input):
        app = system.get_app(app_id)
        dst_node = system.get_node(node_id)

        arrival_rate = calc_received_load(app.id, dst_node.id, system, control_input, environment_input)
        alloc_cpu = control_input.get_allocated_cpu(app.id, dst_node.id)
        service_rate = alloc_cpu / float(app.work_size)

        return DefaultProcessingResult(arrival_rate, service_rate)


class DefaultProcessingResult(ProcessingResult):
    @property
    def delay(self):
        delay = math.inf
        if self.service_rate > self.arrival_rate:
            delay = 1.0 / float(self.service_rate - self.arrival_rate)
        return delay

    @property
    def queue_size(self):
        size = math.inf
        if self.service_rate > self.arrival_rate:
            size = self.arrival_rate / float(self.service_rate - self.arrival_rate)
        return size
