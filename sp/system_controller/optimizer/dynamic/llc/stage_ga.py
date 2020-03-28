from sp.core.heuristic.nsgaii import NSGAII
from sp.system_controller.optimizer.static.moga import MOGAOperator, dominates


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
    pass
