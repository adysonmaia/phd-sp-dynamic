from sp.system_controller.estimator.system import DefaultSystemEstimator
from abc import ABC, abstractmethod


class PlanFinder(ABC):
    def __init__(self,
                 system,
                 environment_inputs,
                 objective,
                 objective_aggregator=None,
                 control_decoder=None,
                 system_estimator=None):

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

    def get_control_input(self, control_sequence, index, system, env_input):
        control_input = control_sequence[index]
        if self.control_decoder is not None:
            control_input = self.control_decoder(system, control_input, env_input)
        return control_input

    @abstractmethod
    def solve(self, control_inputs):
        pass


class Plan:
    def __init__(self, control_sequence=None, fitness=None):
        self.control_sequence = control_sequence
        self.fitness = fitness

    def __getitem__(self, index):
        return self.control_sequence[index]
