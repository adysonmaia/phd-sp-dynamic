from sp.core.model import System, EnvironmentInput
from sp.core.heuristic.brkga import GAIndividual
from sp.system_controller.estimator import SystemEstimator
from abc import ABC, abstractmethod


class InputFinder(ABC):
    """Control Input Finder Abstract Class

    Attributes:
        system (System): current system's state
        environment_inputs (list(EnvironmentInput)): list of predicted environment inputs
        objective (list(function)): list of optimization objective functions
        objective_aggregator (function): objective aggregator function
        system_estimator (SystemEstimator): system estimator
        dominance_func (function): multi-objective dominance function
        pool_size (int): multi-processing pool size
        last_inputs (list(GAIndividual)): list of last control inputs
    """

    def __init__(self,
                 system,
                 environment_inputs,
                 objective,
                 objective_aggregator,
                 system_estimator,
                 dominance_func,
                 pool_size=0,
                 last_inputs=None,
                 **kwargs):
        """Initialization
        """

        self.system = system
        self.environment_inputs = environment_inputs
        self.objective = objective
        self.objective_aggregator = objective_aggregator
        self.system_estimator = system_estimator
        self.dominance_func = dominance_func
        self.pool_size = pool_size
        self.last_inputs = last_inputs

    @property
    def nb_slots(self):
        """Get number of predicted time slots.

        Returns:
            int: number of time slots
        """
        return len(self.environment_inputs)

    def clear_params(self):
        """Clear parameters
        """
        pass

    @abstractmethod
    def solve(self):
        """Execute the heuristic

        Returns:
            list(GAIndividual): list of encoded control inputs
        """
        pass
