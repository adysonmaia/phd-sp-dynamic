from sp.system_controller.optimizer.optimizer import Optimizer
from sp.system_controller.metric import deadline
from sp.core.heuristic.brkga import BRKGA
from .ga_operator import SOGAOperator


class SOGAOptimizer(Optimizer):
    """Single-Objective Genetic Algorithm Optimizer

    See Also: https://ieeexplore.ieee.org/document/9014303

    Attributes:
        objective (function): optimization function.
            It can be any function in the :py:mod:`sp.system_controller.metric` module
        nb_generations (int): maximum number of generations
        population_size (int): population size
        elite_proportion (float): proportion of elite individuals in a population (value between 0 and 1)
        mutant_proportion (float): proportion of mutant individuals in a population (value between 0 and 1)
        elite_probability (float): probability of selecting a elite's gene during a crossover (value between 0 and 1)
        use_heuristic (bool): whether heuristics is used to generate the first population or not
        pool_size (int): multi-processing pool size. If zero, the optimizer doesn't use multi-processing
        timeout (Union[float, None]): maximum execution time of the optimizer. If None, there is no timeout
        load_chunk_distribution (float): load chunk distribution (value between 0 and 1).
            Loads are distributed in chunks where its size is defined by this attribute
    """

    def __init__(self):
        """Initialization
        """
        Optimizer.__init__(self)
        self.objective = None
        self.nb_generations = 100
        self.population_size = 100
        self.elite_proportion = 0.1
        self.mutant_proportion = 0.1
        self.elite_probability = 0.6
        self.load_chunk_distribution = 0.25
        self.use_heuristic = True
        self.pool_size = 4
        self.timeout = None
        self._last_population = None

    def init_params(self):
        """Initialize parameters for a simulation
        """
        if self.objective is None:
            self.objective = deadline.max_deadline_violation

    def clear_params(self):
        """Clear parameters of a simulation
        """
        self._last_population = None

    def solve(self, system, environment_input):
        """Solve the service placement problem

        Args:
            system (sp.core.model.system.System): current system's state
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        Returns:
            sp.system_controller.model.opt_solution.OptSolution: problem solution
        """
        self.init_params()

        ga_operator = SOGAOperator(system=system,
                                   environment_input=environment_input,
                                   objective=self.objective,
                                   use_heuristic=self.use_heuristic,
                                   extra_first_population=self._last_population,
                                   load_chunk_distribution=self.load_chunk_distribution)
        so_ga = BRKGA(operator=ga_operator,
                      nb_generations=self.nb_generations,
                      population_size=self.population_size,
                      elite_proportion=self.elite_proportion,
                      mutant_proportion=self.mutant_proportion,
                      elite_probability=self.elite_probability,
                      timeout=self.timeout,
                      pool_size=self.pool_size)
        population = so_ga.solve()

        last_pop_size = int(round(self.elite_proportion * len(population)))
        if last_pop_size > 0:
            self._last_population = population[:last_pop_size]
        else:
            self._last_population = population

        solution = ga_operator.decode(population[0])
        return solution
