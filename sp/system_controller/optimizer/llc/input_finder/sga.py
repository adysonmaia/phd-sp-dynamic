from .input_finder import InputFinder
from ..plan_finder import PlanFinder, EmptyPlanFinder
from sp.core.heuristic.nsgaii import NSGAII, GAIndividual, GAOperator
from sp.system_controller.optimizer.moga import MOGAOperator


class SGAInputFinder(InputFinder):
    """GA that generates sequences of control inputs
    A sequence can be composed of different control inputs
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
                 **ga_params):

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
        self.plan_finder = EmptyPlanFinder(system=system,
                                           environment_inputs=environment_inputs,
                                           objective=objective,
                                           objective_aggregator=objective_aggregator,
                                           system_estimator=system_estimator,
                                           dominance_func=dominance_func,
                                           pool_size=pool_size)

    def solve(self):
        ga_operator = SGAOperator(plan_finder=self.plan_finder,
                                  sequence_length=self.nb_slots,
                                  use_heuristic=True,
                                  first_population=self.last_inputs)
        ga = NSGAII(operator=ga_operator,
                    dominance_func=self.dominance_func,
                    pool_size=self.pool_size,
                    **self.ga_params)
        population = ga.solve()
        population = list(map(ga_operator.get_control_input, population))
        return population


class SGAOperator(GAOperator):
    """Sequence of Control Inputs GA Operator
    """

    def __init__(self, plan_finder, sequence_length, use_heuristic=True, first_population=None):
        """Initialization
        Args:
            plan_finder (PlanFinder): plan finder
            sequence_length (int): sequence length
            use_heuristic (bool): use heuristic algorithms to generate the first population
            first_population (list(GAIndividual)): list of individuals to be added in the first population
        """
        GAOperator.__init__(self)
        self.plan_finder = plan_finder
        self.sequence_length = sequence_length
        self.use_heuristic = use_heuristic
        self.extended_first_population = first_population

        env_input = plan_finder.environment_inputs[0]
        self._input_ga_operator = MOGAOperator(objective=plan_finder.objective,
                                               system=plan_finder.system,
                                               environment_input=env_input,
                                               use_heuristic=use_heuristic)

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

        if self.extended_first_population is not None:
            for indiv in self.extended_first_population:
                if len(indiv) == self.nb_genes:
                    population.append(indiv)
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
        if individual.is_fitness_valid():
            return individual.fitness
        else:
            sequence = [self.get_control_input(individual, slot) for slot in range(self.sequence_length)]
            plan = self.plan_finder.create_plan(sequence)
            individual.fitness = plan.fitness
            return individual.fitness

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


