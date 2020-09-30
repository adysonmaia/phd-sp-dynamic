from sp.core.heuristic.nsgaii import NSGAII
from sp.system_controller.util import pareto_dominates, preferred_dominates
from sp.hierarchical_controller.global_ctrl.optimizer import GlobalOptimizer
from sp.hierarchical_controller.global_ctrl import metric
from .ga_operator import GlobalMOGAOperator


class GlobalMOGAOptimizer(GlobalOptimizer):
    """Global Multi-Objective Genetic Algorithm Optimizer

    Attributes:
        objective (list(function)): list of optimization functions
        nb_generations (int): maximum number of generations
        population_size (int): population size
        elite_proportion (float): proportion of elite individuals in a population (value between 0 and 1)
        mutant_proportion (float): proportion of mutant individuals in a population (value between 0 and 1)
        elite_probability (float): probability of selecting a elite's gene during a crossover (value between 0 and 1)
        dominance_func (function): multi-objective dominance function.
        stop_threshold (float): MGBM stopping threshold.
        use_heuristic (bool): whether heuristics is used to generate the first population or not
        pool_size (int): multi-processing pool size. If zero, the optimizer doesn't use multi-processing
        timeout (Union[float, None]): maximum execution time of the optimizer. If None, there is no timeout
        load_chunk_distribution (float): load chunk distribution (value between 0 and 1).
            Loads are distributed in chunks where its size is defined by this attribute
    """

    def __init__(self):
        """Initialization
        """
        GlobalOptimizer.__init__(self)
        self.objective = None
        self.nb_generations = 100
        self.population_size = 100
        self.elite_proportion = 0.1
        self.mutant_proportion = 0.1
        self.elite_probability = 0.6
        self.dominance_func = preferred_dominates
        self.stop_threshold = 0.10
        self.use_heuristic = True
        self.timeout = None
        self.pool_size = 4
        self.load_chunk_distribution = 0.25

        self._last_population = None

    def init_params(self):
        """Initialize parameters for a simulation
        """
        if self.objective is None:
            self.objective = [metric.deadline.weighted_avg_deadline_violation,
                              metric.cost.overall_cost,
                              metric.migration.weighted_migration_rate]
        if not isinstance(self.objective, list):
            self.objective = [self.objective]

    def clear_params(self):
        """Clear parameters of a simulation
        """
        self._last_population = None

    def solve(self, system, environment_input):
        """Solve the service placement problem

        Args:
            system (GlobalSystem): current global system's state
            environment_input (GlobalEnvironmentInput): global environment input
        Returns:
            GlobalControlInput: control input
        Raises:
            OptimizerError: error found while solving the problem
        """
        ga_operator = GlobalMOGAOperator(objective=self.objective,
                                         system=system,
                                         environment_input=environment_input,
                                         use_heuristic=self.use_heuristic,
                                         extra_first_population=self._last_population,
                                         load_chunk_distribution=self.load_chunk_distribution)
        mo_ga = NSGAII(operator=ga_operator,
                       nb_generations=self.nb_generations,
                       population_size=self.population_size,
                       elite_proportion=self.elite_proportion,
                       mutant_proportion=self.mutant_proportion,
                       elite_probability=self.elite_probability,
                       stop_threshold=self.stop_threshold,
                       dominance_func=self.dominance_func,
                       timeout=self.timeout,
                       pool_size=self.pool_size)
        population = mo_ga.solve()

        last_pop_size = int(round(self.elite_proportion * len(population)))
        if last_pop_size > 0:
            self._last_population = population[:last_pop_size]
        else:
            self._last_population = population

        solution = ga_operator.decode(population[0])
        return solution



