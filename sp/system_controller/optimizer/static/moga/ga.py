from sp.system_controller.optimizer.static.soga import SOChromosome
from sp.core.heuristic.nsgaii import NSGAII

DEFAULT_DOMINANCE_TOLERANCE = 0.01


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
                 dominance_tolerance=DEFAULT_DOMINANCE_TOLERANCE):

        NSGAII.__init__(self,
                        chromosome=chromosome,
                        population_size=population_size,
                        nb_generations=nb_generations,
                        elite_proportion=elite_proportion,
                        mutant_proportion=mutant_proportion,
                        elite_probability=elite_probability,
                        pool_size=pool_size,
                        stop_threshold=stop_threshold)
        self.dominance_tolerance = dominance_tolerance

    def _dominates(self, fitness_1, fitness_2):
        if len(fitness_1) > 1 and abs(fitness_1[0] - fitness_2[0]) <= self.dominance_tolerance:
            return NSGAII._dominates(self, fitness_1[1:], fitness_2[1:])
        else:
            return fitness_1[0] < fitness_2[0]


class MOChromosome(SOChromosome):
    def __init__(self, objective, system, environment_input, use_heuristic=True):
        SOChromosome.__init__(self,
                              system=system,
                              environment_input=environment_input,
                              objective=objective,
                              use_heuristic=use_heuristic)
        if not isinstance(self.objective, list):
            self.objective = [self.objective]

    def stopping_criteria(self, population):
        return False

    def fitness(self, individual):
        solution = self.decode(individual)
        return [f(self.system, solution, self.environment_input) for f in self.objective]
