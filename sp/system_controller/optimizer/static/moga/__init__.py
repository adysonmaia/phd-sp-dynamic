from sp.controller.solver import Solver, utils
from .ga import MOGA, MOChromosome


class MOGASolver(Solver):
    def __init__(self):
        Solver.__init__(self)
        self.objective = None
        self.nb_generations = 100
        self.population_size = 100
        self.elite_proportion = 0.1
        self.mutant_proportion = 0.1
        self.elite_probability = 0.6
        self.dominance_error = 0.01
        self.stop_threshold = 0.10
        self.use_heuristic = True
        self.pool_size = 4

    def solve(self, system):
        # TODO: set a default objective
        mo_chromosome = MOChromosome(system,
                                     objective=self.objective,
                                     use_heuristic=self.use_heuristic)
        mo_ga = MOGA(mo_chromosome,
                     nb_generations=self.nb_generations,
                     population_size=self.population_size,
                     elite_proportion=self.elite_proportion,
                     mutant_proportion=self.mutant_proportion,
                     elite_probability=self.elite_probability,
                     stop_threshold=self.stop_threshold,
                     dominance_error=self.dominance_error,
                     pool_size=self.pool_size)

        population = mo_ga.solve()
        allocation = mo_chromosome.decode(population[0])
        return utils.alloc_demanded_resources(system, allocation)
