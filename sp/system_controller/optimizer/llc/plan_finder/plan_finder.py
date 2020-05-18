from sp.core.model import System, ControlInput, EnvironmentInput
from sp.core.heuristic import nsgaii
from sp.core.heuristic.brkga import GAIndividual
from sp.system_controller.optimizer.moga import MOGAOperator
from sp.system_controller.estimator import SystemEstimator
from abc import ABC, abstractmethod
from collections import UserList
from functools import cmp_to_key
import multiprocessing as mp


class PlanFinder(ABC):
    """Plan Finder Abstract Class

    Attributes:
        system (System): system
        environment_inputs (list(EnvironmentInput)): list of predicted environment inputs
        objective (list(function)): list of objective functions
        objective_aggregator (function): objective aggregator function
        system_estimator (SystemEstimator): system estimator
        dominance_func (function): multi-objective dominance function
        pool_size (int): multi-processing pool size
    """

    def __init__(self,
                 system,
                 environment_inputs,
                 objective,
                 objective_aggregator,
                 system_estimator,
                 dominance_func,
                 pool_size=0,
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
        self.__pool = None
        self.__map_func = None
        self.__pool_func = None

    @property
    def sequence_length(self):
        """Get sequence length of the plans

        Returns:
            int: length
        """
        return len(self.environment_inputs)

    def __del__(self):
        """Finalizer
        """
        try:
            self.clear_params()
        except AttributeError:
            pass

    def clear_params(self):
        """Clear parameters
        """
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
        """Create a control input plan

        Args:
            control_sequence (list(GAIndividual)): sequence of encoded control inputs
        Returns:
            Plan: plan
        """
        obj_values = [[] for _ in self.objective]
        system = self.system
        for index in range(len(control_sequence)):
            env_input = self.environment_inputs[index]
            control_input = control_sequence[index]
            control_input = decode_control_input(system, control_input, env_input)

            for (func_index, func) in enumerate(self.objective):
                value = func(system, control_input, env_input)
                obj_values[func_index].append(value)

            system = self.system_estimator(system, control_input, env_input)

        fitness = [self.objective_aggregator(value) for value in obj_values]
        return Plan(control_sequence, fitness)

    def create_plans(self, control_sequences):
        """Create a list of plans

        Args:
            control_sequences (list): list of control sequences
        Returns:
            list(Plan): list of plan, one for each control sequence
        """
        self._init_pool()
        plans = list(self.__map_func(self.__pool_func, control_sequences))
        return plans

    def sort_plans(self, plans):
        """Sort a list of plans according to their aggregated objective

        Args:
            plans (list(Plan)): list of plans
        Returns:
            list(Plan): ordered list
        """
        fitnesses = [p.fitness for p in plans]
        fronts, rank = nsgaii.fast_non_dominated_sort(fitnesses, self.dominance_func)
        crwd_dist = nsgaii.crowding_distance(fitnesses, fronts)

        def sort_cmp(plan_1, plan_2):
            index_1 = plans.index(plan_1)
            index_2 = plans.index(plan_2)
            if rank[index_1] < rank[index_2]:
                return -1
            elif (rank[index_1] == rank[index_2]
                  and crwd_dist[index_1] < crwd_dist[index_2]):
                return -1
            else:
                return 1

        return sorted(plans, key=cmp_to_key(sort_cmp))

    @abstractmethod
    def solve(self, control_inputs):
        """Execute the heuristic.
        It finds the best sequences of control inputs

        Args:
            control_inputs (list(GAIndividual)): list of control inputs
        Returns:
            list(Plan): list of plans
        """
        pass


class Plan(UserList):
    """Control Input Plan

    It is a sequence o control inputs that is applied to each prediction window

    Attributes:
        fitness (list): aggregated fitness along the sequence
    """

    def __init__(self, control_sequence=None, fitness=None):
        UserList.__init__(self, control_sequence)
        self.fitness = fitness

    @property
    def control_sequence(self):
        """Get control inputs sequence

        Returns:
            list(GAIndividual): list of encoded control inputs
        """
        return self.data

    @control_sequence.setter
    def control_sequence(self, value):
        """Set control inputs sequence

        Args:
           value (list(GAIndividual)): list of encoded control inputs
        """
        self.data = value

    def is_fitness_valid(self):
        """Check if the fitness is valid

        Returns:
            bool: True if the fitness is valid, False otherwise
        """
        return self.fitness is not None


def decode_control_input(system, encoded_control, environment_input):
    """Decode a control input

    Args:
        system (System): system
        encoded_control (GAIndividual): encoded control input
        environment_input (EnvironmentInput): environment input
    Returns:
        ControlInput: decoded control input
    """
    ga_operator = MOGAOperator(system=system,
                               environment_input=environment_input,
                               objective=None,
                               use_heuristic=False)
    return ga_operator.decode(encoded_control)


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
        control_sequence (list(GAIndividual)): control inputs sequence
    Returns:
        Plan: plan
    """
    global _pf
    return _pf.create_plan(control_sequence)
