from sp.core.heuristic.brkga import GAOperator, GAIndividual
from sp.hierarchical_controller.cluster_ctrl.model import ClusterSystem, ClusterControlInput, ClusterEnvironmentInput
from sp.hierarchical_controller.cluster_ctrl.model import ClusterControlLimit
from sp.hierarchical_controller.cluster_ctrl.estimator import ClusterSystemEstimator
from sp.hierarchical_controller.cluster_ctrl.optimizer.moga.ga_operator import ClusterMOGAOperator
from abc import abstractmethod

DEFAULT_LOAD_CHUNK_DISTRIBUTION = 0.25


class ClusterLLGAOperator(GAOperator):
    """Genetic Operator for Cluster LLGA optimizer

    Attributes:
        system (ClusterSystem): current system's state
        environment_inputs (list(GlobalEnvironmentInput)): predicted environment inputs
        control_limits (list(ClusterControlLimit)): control limits
        objective (list): list of objective functions
        objective_aggregator (function): objective aggregator
        system_estimator (ClusterSystemEstimator): system estimator
        use_heuristic (bool): use heuristic algorithms to generate the first population
        extra_first_population (list(GAIndividual)): list of individuals to be added in the first population
        load_chunk_distribution (float): load chunk distribution (value between 0 and 1).
            Loads are distributed in chunks where its size is defined by this attribute
    """

    def __init__(self,
                 system,
                 environment_inputs,
                 control_limits,
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
        self.control_limits = control_limits
        self.objective = objective
        self.objective_aggregator = objective_aggregator
        self.system_estimator = system_estimator
        self.use_heuristic = use_heuristic
        self.extra_first_population = extra_first_population
        self.load_chunk_distribution = load_chunk_distribution

        if self.load_chunk_distribution is None:
            self.load_chunk_distribution = DEFAULT_LOAD_CHUNK_DISTRIBUTION

    def decode(self, individual):
        """Decode individual to a sequence of control inputs and estimated system's states

        Args:
            individual (GAIndividual): individual

        Returns:
            (list(ClusterControlInput), list(ClusterSystem)): control sequence, system sequence
        """
        decoded_ctrl_sequence = []
        system_sequence = []

        control_sequence = [self.get_encoded_control_input(individual, step)
                            for step in range(self.control_sequence_length)]

        system = self.system
        for index in range(len(control_sequence)):
            env_input = self.environment_inputs[index]
            control_limit = self.control_limits[index]
            control_input = control_sequence[index]
            control_input = self.decode_control_input(system, control_input, env_input, control_limit)

            decoded_ctrl_sequence.append(control_input)
            system_sequence.append(system)

            system = self.system_estimator(system, control_input, env_input)

        return decoded_ctrl_sequence, system_sequence

    def evaluate(self, individual):
        """Evaluate an individual and obtain its fitness

        Args:
            individual (GAIndividual): individual
        Returns:
            list: fitness value
        """
        control_sequence, system_sequence = self.decode(individual)

        obj_values = [[] for _ in self.objective]
        for index in range(len(control_sequence)):
            system = system_sequence[index]
            control_input = control_sequence[index]
            env_input = self.environment_inputs[index]

            for (func_index, func) in enumerate(self.objective):
                value = func(system, control_input, env_input)
                obj_values[func_index].append(value)

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
    def decode_control_input(self, system, encoded_control, environment_input, control_limit):
        """Decode a control input

        Args:
            system (ClusterSystem): system
            encoded_control (GAIndividual): encoded control input
            environment_input (ClusterEnvironmentInput): environment input
            control_limit (ClusterControlLimit): control limit
        Returns:
            ClusterControlInput: decoded control input
        """
        pass


class GeneralClusterLLGAOperator(ClusterLLGAOperator):
    """General Sequence for ClusterLLGAOperator

    """

    def __init__(self, *args, **kwargs):
        """Initialize
        """
        ClusterLLGAOperator.__init__(self, *args, **kwargs)
        self._single_step_operator = ClusterMOGAOperator(objective=self.objective,
                                                         system=self.system,
                                                         environment_input=self.environment_inputs[0],
                                                         control_limit=self.control_limits[0],
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

    def decode_control_input(self, system, encoded_control, environment_input, control_limit):
        """Decode a control input

        Args:
            system (ClusterSystem): system
            encoded_control (GAIndividual): encoded control input
            environment_input (ClusterEnvironmentInput): environment input
            control_limit (ClusterControlLimit): control limit
        Returns:
            ClusterControlInput: decoded control input
        """
        ga_operator = ClusterMOGAOperator(objective=self.objective,
                                          system=system,
                                          environment_input=environment_input,
                                          control_limit=control_limit,
                                          use_heuristic=self.use_heuristic,
                                          load_chunk_distribution=self.load_chunk_distribution)

        decoded_ctrl_input = ga_operator.decode(encoded_control)
        return decoded_ctrl_input


class SimpleClusterLLGAOperator(GeneralClusterLLGAOperator):
    """Simple Sequence for ClusterLLGAOperator

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
