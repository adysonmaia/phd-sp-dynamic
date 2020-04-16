from sp.core.heuristic.nsgaii import NSGAII
from sp.system_controller.optimizer.static.moga import MOGAOperator, preferred_dominates
from sp.system_controller.optimizer.static.soga import indiv_gen


class StageGA(NSGAII):
    def first_population(self, apply_selection=False):
        """Generate the individuals of the first generation
        Args:
            apply_selection (bool): if the selection operation will be applied for the generated individuals
        Returns:
            list(GAIndividual): list of sorted individuals
        """
        self.current_population = NSGAII.first_population(self, apply_selection=apply_selection)
        return self.current_population

    def select_individuals(self, population=None):
        """Select best individuals in a population
        Args:
            population (list(GAIndividual)): list of individuals
        Returns:
            list(GAIndividual): selected individuals
        """
        if population is None:
            population = self.current_population
        self.current_population = NSGAII.select_individuals(self, population)
        return self.current_population

    def next_population(self, population=None, apply_selection=False):
        """Generate the next population through crossover and mutation operations in the current population
        Args:
            population (list): sorted population
            apply_selection (bool): if the selection operation will be applied in the next population
        Returns:
            list: list of individuals of the next population
        """
        if population is None:
            population = self.current_population
        self.current_population = NSGAII.next_population(self, population, apply_selection=apply_selection)
        return self.current_population

    def should_stop(self, population=None):
        """Verify whether the GA should stop or not
        Args:
            population (list(GAIndividual)): population of the current generation
        Returns:
            bool: True if algorithm should stop, False otherwise
        """
        if population is None:
            population = self.current_population
        return NSGAII.should_stop(self, population)


class StageGAOperator(MOGAOperator):
    """Stage GA Operator
    """
    def __init__(self, extended_first_population=None, **kwargs):
        """Initialization
        Args:
            extended_first_population (list): extended list of first population
            **kwargs: ga operator params
        """
        self.extended_first_population = extended_first_population
        MOGAOperator.__init__(self, **kwargs)

    def first_population(self):
        """Generate some specific individuals for the first population based on heuristic algorithms
        Returns:
            individuals (list(GAIndividual)): list of individuals
        """
        pop = MOGAOperator.first_population(self)
        if self.extended_first_population is not None:
            pop += [indiv.clear_copy() for indiv in self.extended_first_population]
        return pop


class MultiStageGA(StageGA):
    """Multi Stage GA
    """
    pass


class MultiStageGAOperator(StageGAOperator):
    """Multi Stage GA Operator
    """

    def __init__(self, plan_finder, nb_stages, **kwargs):
        """ Initialization
        Args:
            plan_finder (sp.system_controller.optimizer.dynamic.llc.plan_finder.plan_finder.PlanFinder): plan finder
            nb_stages (int): number of stages
            **kwargs: ga params
        """
        StageGAOperator.__init__(self, **kwargs)
        self.plan_finder = plan_finder
        self.nb_stages = nb_stages

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
            sequence = [individual] * self.nb_stages
            plan = self.plan_finder.create_plan(sequence)
            individual.fitness = plan.fitness
            return individual.fitness
