from .input_finder import InputFinder
from ..plan_finder import PlanFinder, EmptyPlanFinder
from sp.core.heuristic.nsgaii import NSGAII, GAIndividual, GAOperator
from sp.system_controller.optimizer.moga import MOGAOperator


class SGAInputFinder(InputFinder):
    """Sequence of control inputs GA Input Finder

    It is a genetic algorithm that generates sequences of control inputs.
    A sequence can be composed of different control inputs

    Attributes:
        ga_params (dict): initialization parameters of :py:class:`~sp.core.heuristic.nsgaii.NSGAII` class
    """

    def __init__(self,
                 system,
                 environment_inputs,
                 objective,
                 objective_aggregator,
                 system_estimator,
                 dominance_func,
                 pool_size,
                 last_inputs,
                 load_chunk_distribution=None,
                 **ga_params):
        """Initialization
        """

        InputFinder.__init__(self,
                             system=system,
                             environment_inputs=environment_inputs,
                             objective=objective,
                             objective_aggregator=objective_aggregator,
                             system_estimator=system_estimator,
                             dominance_func=dominance_func,
                             pool_size=pool_size,
                             last_inputs=last_inputs)
        self.ga_params = ga_params
        self._plan_finder = EmptyPlanFinder(system=system,
                                            environment_inputs=environment_inputs,
                                            objective=objective,
                                            objective_aggregator=objective_aggregator,
                                            system_estimator=system_estimator,
                                            dominance_func=dominance_func,
                                            pool_size=pool_size,
                                            load_chunk_distribution=load_chunk_distribution)

    def solve(self):
        """Execute the heuristic

        Returns:
            list(GAIndividual): list of encoded control inputs
        """
        ga_operator = SGAOperator(plan_finder=self._plan_finder,
                                  sequence_length=self.nb_slots,
                                  use_heuristic=True,
                                  extra_first_population=self.last_inputs)
        ga = NSGAII(operator=ga_operator,
                    dominance_func=self.dominance_func,
                    pool_size=self.pool_size,
                    **self.ga_params)

        if self.last_inputs is not None:
            last_pop_size = int(round(ga.elite_proportion * len(self.last_inputs)))
            if last_pop_size > 0:
                ga_operator.extra_first_population = self.last_inputs[:last_pop_size]

        population = ga.solve()
        population = list(map(ga_operator.get_control_input, population))
        return population


class SGAOperator(GAOperator):
    """Sequence of Control Inputs GA Operator

    Attributes:
        plan_finder (PlanFinder): plan finder
        sequence_length (int): control inputs sequence length
        use_heuristic (bool): use heuristic algorithms to generate the first population
        extra_first_population (list(GAIndividual)): list of individuals to be added in the first population
    """

    def __init__(self, plan_finder, sequence_length, use_heuristic=True, extra_first_population=None):
        """Initialization
        """
        GAOperator.__init__(self)
        self.plan_finder = plan_finder
        self.sequence_length = sequence_length
        self.use_heuristic = use_heuristic
        self.extra_first_population = extra_first_population

        env_input = plan_finder.environment_inputs[0]
        self._input_ga_operator = MOGAOperator(objective=plan_finder.objective,
                                               system=plan_finder.system,
                                               environment_input=env_input,
                                               use_heuristic=use_heuristic,
                                               load_chunk_distribution=plan_finder.load_chunk_distribution)

    @property
    def nb_genes(self):
        """Number of genes in the chromosome

        Returns:
            int: number of genes in a individual's chromosome
        """
        return self.nb_genes_per_input * self.sequence_length

    @property
    def nb_genes_per_input(self):
        """Number of genes per control input
        Chromosome represents a sequence of control inputs

        Returns:
            int: number of genes
        """
        return self._input_ga_operator.nb_genes

    def first_population(self):
        """Generate some specific individuals for the first population based on heuristic algorithms

        Returns:
            individuals (list(GAIndividual)): list of individuals
        """
        input_population = self._input_ga_operator.first_population()
        population = []

        for indiv in input_population:
            sequence = GAIndividual(indiv * self.sequence_length)
            population.append(sequence)

        if self.extra_first_population is not None:
            for indiv in self.extra_first_population:
                if len(indiv) == self.nb_genes:
                    population.append(indiv.clear_copy())
                elif len(indiv) == self.nb_genes_per_input:
                    sequence = GAIndividual(indiv * self.sequence_length)
                    population.append(sequence)

        return population

    def evaluate(self, individual):
        """Evaluate an individual and obtain its fitness

        Args:
            individual (GAIndividual): individual
        Returns:
            object: fitness value
        """
        sequence = [self.get_control_input(individual, slot) for slot in range(self.sequence_length)]
        plan = self.plan_finder.create_plan(sequence)
        return plan.fitness

    def get_control_input(self, individual, slot=0):
        """Get the control input in a specific time slot stored in an individual

        Args:
            individual (GAIndividual): individual representing a sequence of control inputs
            slot (int): time slot
        Returns:
            GAIndividual: individual representing a control input
        """
        start = slot * self.nb_genes_per_input
        end = start + self.nb_genes_per_input
        control_input = individual[start:end]
        return GAIndividual(control_input)


