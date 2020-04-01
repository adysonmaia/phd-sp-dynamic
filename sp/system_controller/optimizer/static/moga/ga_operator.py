from sp.system_controller.optimizer.static.soga import SOGAOperator
from sp.core.heuristic.nsgaii import pareto_dominates

# DEFAULT_DOMINANCE_TOLERANCE = 0.00001
DEFAULT_DOMINANCE_TOLERANCE = 0.0


class MOGAOperator(SOGAOperator):
    """Genetic Operator for MOGA optimizer
    """

    def __init__(self, **soga_operator_params):
        """Initialization
        Args:
            **soga_operator_params: initialization parameters for
                :py:class:`sp.system_controller.optimizer.static.soga.SOGAOperator` algorithm
        """
        SOGAOperator.__init__(self, **soga_operator_params)
        if not isinstance(self.objective, list):
            self.objective = [self.objective]

    def should_stop(self, population):
        """Verify whether genetic algorithm should stop or not
        Args:
           population (list(GAIndividual)): population of the current generation
        Returns:
           bool: True if genetic algorithm should stop, False otherwise
        """
        return False

    def evaluate(self, individual):
        """Evaluate an individual and obtain its fitness
        Args:
            individual (GAIndividual): individual
        Returns:
            object: fitness value
        """
        solution = self.decode(individual)
        return [f(self.system, solution, self.environment_input) for f in self.objective]


def preferred_dominates(fitness_1, fitness_2, dominance_tolerance=DEFAULT_DOMINANCE_TOLERANCE):
    """ Preferred dominance operator
    Args:
        fitness_1 (list): fitness of the first individual
        fitness_2 (list): fitness of the second individual
        dominance_tolerance (float): tolerance
    Returns:
        bool: True if first individual dominates the second individual
    """
    if len(fitness_1) > 1 and abs(fitness_1[0] - fitness_2[0]) <= dominance_tolerance:
        return pareto_dominates(fitness_1[1:], fitness_2[1:])
    else:
        return fitness_1[0] < fitness_2[0]
