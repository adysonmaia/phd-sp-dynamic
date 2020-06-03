from sp.core.estimator import Estimator
from sp.core.model import System, EnvironmentInput, ControlInput
from sp.system_controller.util.calc import calc_received_load
from abc import ABC, abstractmethod
import math


class ProcessingEstimator(Estimator):
    """Processing Estimator Abstract Class
    """

    @abstractmethod
    def calc(self, app_id, node_id, system, control_input, environment_input):
        """Estimate the state of the processor

        Args:
            app_id (int): application's id
            node_id (int): node's id
            system (System): system
            control_input (ControlInput): control input
            environment_input (EnvironmentInput):  environment input
        Returns:
            ProcessingResult: processor's state
        """
        pass


class ProcessingResult(ABC):
    """Processing Estimation Result Abstract Class.
    It saves the state of the processor

    Attributes:
        arrival_rate (float): arrival rate
        service_rate (float): service rate
    """

    def __init__(self, arrival_rate, service_rate):
        """Initialization

        Args:
            arrival_rate (float): arrival rate
            service_rate (float): service rate
        """
        ABC.__init__(self)
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate

    @property
    @abstractmethod
    def delay(self):
        """Processing delay

        Returns:
            float: delay
        """
        pass

    @property
    @abstractmethod
    def queue_size(self):
        """Processing queue's size

        Returns:
            float: size
        """
        pass


class DefaultProcessingEstimator(ProcessingEstimator):
    """Default Processing Estimator
    """

    def calc(self, app_id, node_id, system, control_input, environment_input):
        """Estimate the state of the processor

        Args:
            app_id (int): application's id
            node_id (int): node's id
            system (System): system
            control_input (ControlInput): control input
            environment_input (EnvironmentInput):  environment input
        Returns:
            DefaultProcessingResult: processor's state
        """
        app = system.get_app(app_id)
        dst_node = system.get_node(node_id)

        arrival_rate = calc_received_load(app.id, dst_node.id, system, control_input, environment_input)
        alloc_cpu = control_input.get_allocated_cpu(app.id, dst_node.id)
        service_rate = alloc_cpu / float(app.work_size)

        return DefaultProcessingResult(arrival_rate, service_rate)


class DefaultProcessingResult(ProcessingResult):
    """Default Processing Estimation Result.
    It follows the M/M/1 queueing model

    See Also: https://en.wikipedia.org/wiki/M/M/1_queue
    """

    @property
    def delay(self):
        """Processing delay

        Returns:
            float: delay
        """
        delay = math.inf
        if self.service_rate > self.arrival_rate:
            delay = 1.0 / float(self.service_rate - self.arrival_rate)
        elif self.service_rate == self.arrival_rate == 0.0:
            delay = 0.0
        return delay

    @property
    def queue_size(self):
        """Processing queue's size

        Returns:
            float: size
        """
        size = math.inf
        if self.service_rate > self.arrival_rate > 0.0:
            p = self.arrival_rate / float(self.service_rate)
            size = (p ** 2) / (1.0 - p)
            # size = p / (1.0 - p)
        elif self.arrival_rate == 0.0:
            size = 0.0
        return size
