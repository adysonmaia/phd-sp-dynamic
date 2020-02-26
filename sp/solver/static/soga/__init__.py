from sp.solver import Solver, utils
from sp.heuristic.brkga import BRKGA
from .chromosome import SOGAChromosome


class SOGASolver(Solver):
    def __init__(self):
        Solver.__init__(self)
        self.objective = None
        self.nb_generations = 100
        self.population_size = 100
        self.elite_proportion = 0.1
        self.mutant_proportion = 0.1
        self.elite_probability = 0.6
        self.use_heuristic = True
        self.pool_size = 4

    def solve(self, system):
        soga_chromosome = SOGAChromosome(system,
                                         objective=self.objective,
                                         use_heuristic=self.use_heuristic)
        ga = BRKGA(soga_chromosome,
                   nb_generations=self.nb_generations,
                   population_size=self.population_size,
                   elite_proportion=self.elite_proportion,
                   mutant_proportion=self.mutant_proportion,
                   elite_probability=self.elite_probability,
                   pool_size=self.pool_size)

        population = ga.solve()
        alloc = soga_chromosome.decode(population[0])
        utils.alloc_demanded_resources(system, alloc)
        return alloc
