from sp.system_controller.optimizer import Optimizer
from sp.system_controller.metric.static import deadline, availability, cost
from .ga import MOGA, MOChromosome


class MOGAOptimizer(Optimizer):
    def __init__(self):
        Optimizer.__init__(self)
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
        if self.objective is None:
            self.objective = [
                deadline.max_deadline_violation,
                cost.overall_cost,
                availability.avg_unavailability,
            ]

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
        solution = mo_chromosome.decode(population[0])
        return solution
