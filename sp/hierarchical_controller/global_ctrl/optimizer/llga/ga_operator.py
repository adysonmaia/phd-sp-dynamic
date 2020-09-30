from sp.core.heuristic.brkga import GAOperator, GAIndividual
from sp.hierarchical_controller.global_ctrl.model import GlobalSystem, GlobalControlInput, GlobalEnvironmentInput
from sp.hierarchical_controller.global_ctrl.optimizer.moga.ga_operator import GlobalMOGAOperator
from sp.hierarchical_controller.global_ctrl.estimator.system import GlobalSystemEstimator
from abc import ABC, abstractmethod


DEFAULT_LOAD_CHUNK_DISTRIBUTION = 0.25


class GlobalLLGAOperator(GAOperator):
    """Genetic Operator for Global LLGA optimizer

    Attributes:
        system (GlobalSystem): current system's state
        environment_inputs (list(GlobalEnvironmentInput)): predicted environment inputs
        objective (list): list of objective functions
        objective_aggregator (function): objective aggregator
        system_estimator (GlobalSystemEstimator): global system estimator
        use_heuristic (bool): use heuristic algorithms to generate the first population
        extra_first_population (list(GAIndividual)): list of individuals to be added in the first population
        load_chunk_distribution (float): load chunk distribution (value between 0 and 1).
            Loads are distributed in chunks where its size is defined by this attribute
    """

    def __init__(self,
                 system,
                 environment_inputs,
                 objective,
                 objective_aggregator,
                 system_estimator,
                 use_heuristic=True,
                 extra_first_population=None,
                 load_chunk_distribution=None):
        """Initialization
        """
        GAOperator.__init__(self)
        self.system = system
        self.environment_inputs = environment_inputs
        self.objective = objective
        self.objective_aggregator = objective_aggregator
        self.system_estimator = system_estimator
        self.use_heuristic = use_heuristic
        self.extra_first_population = extra_first_population
        self.load_chunk_distribution = load_chunk_distribution
        if self.load_chunk_distribution is None:
            self.load_chunk_distribution = DEFAULT_LOAD_CHUNK_DISTRIBUTION

    def evaluate(self, individual):
        """Evaluate an individual and obtain its fitness

        Args:
            individual (GAIndividual): individual
        Returns:
            list: fitness value
        """
        control_sequence = [self.get_encoded_control_input(individual, step)
                            for step in range(self.control_sequence_length)]

        obj_values = [[] for _ in self.objective]
        system = self.system
        for index in range(len(control_sequence)):
            env_input = self.environment_inputs[index]
            control_input = control_sequence[index]
            control_input = self.decode_control_input(system, control_input, env_input)

            for (func_index, func) in enumerate(self.objective):
                value = func(system, control_input, env_input)
                obj_values[func_index].append(value)

            system = self.system_estimator(system, control_input, env_input)

        fitness = [self.objective_aggregator(value) for value in obj_values]
        return fitness

    @property
    def control_sequence_length(self):
        return len(self.environment_inputs)

    @abstractmethod
    def get_encoded_control_input(self, individual, step=0):
        """Get the control input in a specific time step stored in an individual

        Args:
            individual (GAIndividual): individual representing a sequence of control inputs
            step (int): time step
        Returns:
            GAIndividual: individual representing a control input in a single time step
        """
        pass

    @abstractmethod
    def decode_control_input(self, system, encoded_control, environment_input):
        """Decode a control input

        Args:
            system (GlobalSystem): system
            encoded_control (GAIndividual): encoded control input
            environment_input (GlobalEnvironmentInput): environment input
        Returns:
            GlobalControlInput: decoded control input
        """
        pass


class GeneralGlobalLLGAOperator(GlobalLLGAOperator):
    """General Sequence for GlobalLLGAOperator

    """

    def __init__(self, *args, **kwargs):
        """Initialize
        """
        GlobalLLGAOperator.__init__(self, *args, **kwargs)
        self._single_step_operator = GlobalMOGAOperator(objective=self.objective,
                                                        system=self.system,
                                                        environment_input=self.environment_inputs[0],
                                                        use_heuristic=self.use_heuristic,
                                                        load_chunk_distribution=self.load_chunk_distribution)

    @property
    def nb_genes(self):
        """Number of genes of an individual's chromosome

        Returns:
            int: number of genes
        """
        return self.nb_genes_per_time_step * self.control_sequence_length

    @property
    def nb_genes_per_time_step(self):
        """Number of genes per control input
        Chromosome represents a sequence of control inputs

        Returns:
            int: number of genes
        """
        return self._single_step_operator.nb_genes

    def first_population(self):
        """Generate some specific individuals for the first population based on heuristic algorithms

        Returns:
            individuals (list(GAIndividual)): list of individuals
        """
        input_population = self._single_step_operator.first_population()
        population = []

        for indiv in input_population:
            sequence = GAIndividual(indiv * self.control_sequence_length)
            population.append(sequence)

        if self.extra_first_population is not None:
            for indiv in self.extra_first_population:
                if len(indiv) == self.nb_genes:
                    population.append(indiv.clear_copy())
                elif len(indiv) == self.nb_genes_per_time_step:
                    sequence = GAIndividual(indiv * self.control_sequence_length)
                    population.append(sequence)

        return population

    def get_encoded_control_input(self, individual, step=0):
        """Get the control input in a specific time step stored in an individual

        Args:
            individual (GAIndividual): individual representing a sequence of control inputs
            step (int): time step
        Returns:
            GAIndividual: individual representing a control input in a single time step
        """
        start = step * self.nb_genes_per_time_step
        end = start + self.nb_genes_per_time_step
        control_input = individual[start:end]
        return GAIndividual(control_input)

    def decode_control_input(self, system, encoded_control, environment_input):
        """Decode a control input

        Args:
            system (GlobalSystem): system
            encoded_control (GAIndividual): encoded control input
            environment_input (GlobalEnvironmentInput): environment input
        Returns:
            GlobalControlInput: decoded control input
        """
        ga_operator = GlobalMOGAOperator(objective=self.objective,
                                         system=system,
                                         environment_input=environment_input,
                                         use_heuristic=self.use_heuristic,
                                         load_chunk_distribution=self.load_chunk_distribution)
        decoded_ctrl_input = ga_operator.decode(encoded_control)
        return decoded_ctrl_input


class SimpleGlobalLLGAOperator(GeneralGlobalLLGAOperator):
    """Simple Sequence for GlobalLLGAOperator

    """

    @property
    def nb_genes(self):
        """Number of genes of an individual's chromosome

        Returns:
            int: number of genes
        """
        return self._single_step_operator.nb_genes

    def first_population(self):
        """Generate some specific individuals for the first population based on heuristic algorithms

        Returns:
            individuals (list(GAIndividual)): list of individuals
        """
        population = []
        if self.extra_first_population is not None:
            for indiv in self.extra_first_population:
                if len(indiv) == self.nb_genes:
                    population.append(indiv.clear_copy())
                elif len(indiv) > self.nb_genes:
                    simple_indiv = GAIndividual(indiv[:self.nb_genes])
                    population.append(simple_indiv)

        population += self._single_step_operator.first_population()
        return population

    def get_encoded_control_input(self, individual, step=0):
        """Get the control input in a specific time step stored in an individual

        Args:
            individual (GAIndividual): individual representing a sequence of control inputs
            step (int): time step
        Returns:
            GAIndividual: individual representing a control input in a single time step
        """
        return individual
