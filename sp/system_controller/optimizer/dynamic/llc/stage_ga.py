from sp.core.heuristic.nsgaii import NSGAII
from sp.system_controller.optimizer.static.moga import MOGA, MOChromosome

INF = float("inf")


class StageGA(MOGA):
    def __init__(self,
                 system,
                 environment_input,
                 objective,
                 population_size,
                 nb_generations,
                 elite_proportion,
                 mutant_proportion,
                 elite_probability,
                 pool_size,
                 stop_threshold,
                 dominance_tolerance,
                 use_heuristic):

        chromosome = StageChromosome(system=system,
                                     objective=objective,
                                     environment_input=environment_input,
                                     use_heuristic=use_heuristic)
        MOGA.__init__(self,
                      chromosome=chromosome,
                      population_size=population_size,
                      nb_generations=nb_generations,
                      elite_proportion=elite_proportion,
                      mutant_proportion=mutant_proportion,
                      elite_probability=elite_probability,
                      pool_size=pool_size,
                      stop_threshold=stop_threshold,
                      dominance_tolerance=dominance_tolerance)

        self._current_pop = None
        self._pop_fitness = None
        self._nb_objectives = len(objective)

    def _init_params(self):
        NSGAII._init_params(self)
        self._current_pop = None
        self._init_pop_fitness()

    def _init_pop_fitness(self):
        fitness = [INF] * self._nb_objectives
        self._pop_fitness = [fitness for _ in range(self.population_size)]

    def _get_fitness(self, individual):
        if self._pop_fitness is not None:
            index = self._current_pop.index(individual)
            return self._pop_fitness[index]
        else:
            return MOGA._get_fitness(self, individual)

    def _get_fitnesses(self, population):
        if self._pop_fitness is None:
            self._pop_fitness = MOGA._get_fitnesses(self, population)
        return self._pop_fitness

    @property
    def current_population(self):
        return self._current_pop

    def set_fitness(self, individual, value):
        index = self._current_pop.index(individual)
        self._pop_fitness[index] = value

    def get_fitness(self, individual):
        return self._get_fitness(individual)

    def dominates(self, fitness_1, fitness_2):
        return self._dominates(fitness_1, fitness_2)

    def is_stopping_criteria_met(self):
        return self._stopping_criteria(self._current_pop)

    def next_population(self):
        next_pop = None
        if self._current_pop is None:
            self._init_params()
            next_pop = self._gen_first_population(classify=False)
        else:
            # Select individuals with best fitness for next generation
            self._current_pop = self._classify_population(self._current_pop)
            self._current_pop = self._current_pop[:self.population_size]
            next_pop = self._gen_next_population(self._current_pop, classify=False)

        self._current_pop = next_pop
        self._init_pop_fitness()
        return next_pop


class StageChromosome(MOChromosome):
    def __init__(self, system, environment_input, objective=None, use_heuristic=True):
        MOChromosome.__init__(self,
                              system=system,
                              environment_input=environment_input,
                              objective=objective,
                              use_heuristic=use_heuristic)



