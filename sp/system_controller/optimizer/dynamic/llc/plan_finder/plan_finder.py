from sp.system_controller.estimator.system import DefaultSystemEstimator
from abc import ABC, abstractmethod
from collections import UserList
import multiprocessing as mp


class PlanFinder(ABC):
    def __init__(self,
                 system,
                 environment_inputs,
                 objective,
                 objective_aggregator=None,
                 control_decoder=None,
                 system_estimator=None,
                 pool_size=0):

        self.system = system
        self.environment_inputs = environment_inputs
        self.objective = objective
        self.objective_aggregator = objective_aggregator
        self.control_decoder = control_decoder
        self.system_estimator = system_estimator

        if self.objective_aggregator is None:
            self.objective_aggregator = sum

        if self.system_estimator is None:
            self.system_estimator = DefaultSystemEstimator()

        self.pool_size = pool_size
        self.__pool = None
        self.__map_func = None
        self.__pool_func = None

    def __del__(self):
        self._clear_pool()

    def _init_pool(self):
        """Initialize the multiprocessing pool
        """
        if self.__pool is not None:
            return

        self.__pool = None
        self.__map_func = map
        self.__pool_func = self.create_plan
        if self.pool_size > 0:
            try:
                # Require UNIX fork to work
                mp_ctx = mp.get_context("fork")
                self.pool_size = min(self.pool_size, mp_ctx.cpu_count())
                self.__pool = mp_ctx.Pool(processes=self.pool_size,
                                          initializer=_init_pool,
                                          initargs=[self])
                self.__map_func = self.__pool.map
                self.__pool_func = _create_plan
            except ValueError:
                pass

    def _clear_pool(self):
        """Terminate the multiprocessing pool
        """
        if self.__pool is not None:
            self.__pool.terminate()
            self.__pool = None
            self.__map_func = None
            self.__pool_func = None

    def create_plan(self, control_sequence):
        obj_values = [[] for _ in self.objective]
        system = self.system
        for index in range(len(control_sequence)):
            env_input = self.environment_inputs[index]
            control_input = self.get_control_input(control_sequence, index, system, env_input)

            for (func_index, func) in enumerate(self.objective):
                value = func(system, control_input, env_input)
                obj_values[func_index].append(value)

            system = self.system_estimator(system, control_input, env_input)

        fitness = [self.objective_aggregator(value) for value in obj_values]
        return Plan(control_sequence, fitness)

    def create_plans(self, control_sequences):
        self._init_pool()
        plans = list(self.__map_func(self.__pool_func, control_sequences))
        return plans

    def get_control_input(self, control_sequence, index, system, env_input):
        control_input = control_sequence[index]
        if self.control_decoder is not None:
            control_input = self.control_decoder(system, control_input, env_input)
        return control_input

    @abstractmethod
    def solve(self, control_inputs):
        pass


class Plan(UserList):
    def __init__(self, control_sequence=None, fitness=None):
        UserList.__init__(self, control_sequence)
        self.fitness = fitness

    @property
    def control_sequence(self):
        return self.data

    @control_sequence.setter
    def control_sequence(self, value):
        self.data = value

    def is_fitness_valid(self):
        return self.fitness is not None


def _init_pool(plan_finder):
    """Initialize a sub-process to create a plan
    Args:
        plan_finder (PlanFinder): plan finder
    """
    global _pf
    _pf = plan_finder


def _create_plan(control_sequence):
    """Calculate the fitness of an individual
    Args:
        control_sequence (list): control input sequence
    Returns:
        Plan: plan
    """
    global _pf
    return _pf.create_plan(control_sequence)
