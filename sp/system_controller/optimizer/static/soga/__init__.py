from sp.system_controller.optimizer import Optimizer
from sp.system_controller.metric.static import deadline
from sp.core.heuristic.brkga import BRKGA

from .chromosome import SOChromosome
from . import individual_generator as indiv_gen


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

    def solve(self, system):
        if self.objective is None:
            self.objective = deadline.max_deadline_violation

        so_chromosome = SOChromosome(system,
                                     objective=self.objective,
                                     use_heuristic=self.use_heuristic)
        so_ga = BRKGA(so_chromosome,
                      nb_generations=self.nb_generations,
                      population_size=self.population_size,
                      elite_proportion=self.elite_proportion,
                      mutant_proportion=self.mutant_proportion,
                      elite_probability=self.elite_probability,
                      pool_size=self.pool_size)

        population = so_ga.solve()
        solution = so_chromosome.decode(population[0])
        return solution
