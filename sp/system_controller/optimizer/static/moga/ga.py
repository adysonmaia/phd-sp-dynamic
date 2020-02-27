from sp.system_controller.optimizer.static.soga import SOChromosome
from sp.core.heuristic.nsgaii import NSGAII

DEFAULT_DOMINANCE_ERROR = 0.01


class MOGA(NSGAII):
    def __init__(self,
                 chromosome,
                 population_size,
                 nb_generations,
                 elite_proportion,
                 mutant_proportion,
                 elite_probability,
                 pool_size,
                 stop_threshold,
                 dominance_error=DEFAULT_DOMINANCE_ERROR):

        NSGAII.__init__(self, chromosome, population_size, nb_generations,
                        elite_proportion, mutant_proportion, elite_probability,
                        pool_size, stop_threshold)
        self.dominance_error = dominance_error

    def _dominates(self, fitness_1, fitness_2):
        if len(fitness_1) > 1 and abs(fitness_1[0] - fitness_2[0]) <= self.dominance_error:
            return NSGAII._dominates(self, fitness_1[1:], fitness_2[1:])
        else:
            return fitness_1[0] < fitness_2[0]


class MOChromosome(SOChromosome):
    def __init__(self, system, objective, use_heuristic=True):
        SOChromosome.__init__(self, system, objective=objective, use_heuristic=use_heuristic)
        self.objective = list(self.objective)

    def stopping_criteria(self, population):
        return False

    def fitness(self, individual):
        solution = self.decode(individual)
        return [f(*solution) for f in self.objective]
