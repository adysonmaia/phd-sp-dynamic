from sp.system_controller.optimizer.optimizer import Optimizer
from sp.system_controller.metric import deadline
from sp.core.heuristic.brkga import BRKGA
from .ga_operator import SOGAOperator


class SOGAOptimizer(Optimizer):
    def __init__(self):
        Optimizer.__init__(self)
        self.objective = None
        self.nb_generations = 100
        self.population_size = 100
        self.elite_proportion = 0.1
        self.mutant_proportion = 0.1
        self.elite_probability = 0.6
        self.use_heuristic = True
        self.pool_size = 4
        self.timeout = None
        self._last_population = None

    def init_params(self):
        if self.objective is None:
            self.objective = deadline.max_deadline_violation

    def clear_params(self):
        self._last_population = None

    def solve(self, system, environment_input):
        self.init_params()

        ga_operator = SOGAOperator(system=system,
                                   environment_input=environment_input,
                                   objective=self.objective,
                                   use_heuristic=self.use_heuristic,
                                   first_population=self._last_population)
        so_ga = BRKGA(operator=ga_operator,
                      nb_generations=self.nb_generations,
                      population_size=self.population_size,
                      elite_proportion=self.elite_proportion,
                      mutant_proportion=self.mutant_proportion,
                      elite_probability=self.elite_probability,
                      timeout=self.timeout,
                      pool_size=self.pool_size)
        population = so_ga.solve()
        self._last_population = population
        solution = ga_operator.decode(population[0])
        return solution
