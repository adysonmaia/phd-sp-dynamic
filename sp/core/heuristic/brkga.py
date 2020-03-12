import random
import multiprocessing as mp


def _init_pool(genetic_algo):
    """Initialize a sub-process to calculate an individual fitness
    Args:
        genetic_algo (BRKGA): a genetic algorithm object
    """
    global _ga
    _ga = genetic_algo


def _get_fitness(indiv):
    """Calculate the fitness of an individual
    Args:
        indiv (list): individual
    Returns:
        float: fitness value
    """
    global _ga
    return _ga._get_fitness(indiv)


class BRKGA:
    """ Biased Random Key Genetic Algorithm
    See also:
    https://link.springer.com/article/10.1007/s10732-010-9143-1
    """

    def __init__(self,
                 chromosome,
                 population_size,
                 nb_generations,
                 elite_proportion,
                 mutant_proportion,
                 elite_probability=None,
                 pool_size=0):
        """Initialize method
        Args:
            chromosome (BRKGAChromosome): chromosome representation
            population_size (int): population size
            nb_generations (int): maximum number of generations
            elite_proportion (float): proportion of the number of elite
                                      individuals in the population,
                                      value in [0, 1]
            mutant_proportion (float): proportion of the number of mutant
                                       individuals in the population,
                                       value in [0, 1]
            elite_probability (float): probability of a elite gene to be
                                       selected during crossover
            pool_size (int): number of processes for parallelisms
        """

        self.chromosome = chromosome
        self.nb_genes = chromosome.nb_genes
        self.population_size = population_size
        self.nb_generations = nb_generations
        self.elite_proportion = elite_proportion
        self.mutant_proportion = mutant_proportion
        self._elite_size = int(round(self.elite_proportion * self.population_size))
        self._mutant_size = int(round(self.mutant_proportion * self.population_size))
        self.elite_probability = elite_probability

        if self.elite_probability is None:
            self.elite_probability = self._elite_size / float(self.population_size)

        self.pool_size = pool_size
        self._pool = None
        self._map_func = None
        self._fitness_func = None

    def _init_params(self):
        """Initialize parameters before starting the genetic algorithm
        """
        self._elite_size = int(round(self.elite_proportion * self.population_size))
        self._mutant_size = int(round(self.mutant_proportion * self.population_size))
        self._init_pool()
        self.chromosome.init_params()

    def _init_pool(self):
        """Initialize the multiprocessing pool
        """
        self._clean_pool()

        self._pool = None
        self._map_func = map
        self._fitness_func = self._get_fitness
        if self.pool_size > 0:
            try:
                # Require UNIX fork to work
                mp_ctx = mp.get_context("fork")
                self.pool_size = min(self.pool_size, mp_ctx.cpu_count())
                self._pool = mp_ctx.Pool(processes=self.pool_size,
                                         initializer=_init_pool,
                                         initargs=[self])
                self._map_func = self._pool.map
                self._fitness_func = _get_fitness
            except ValueError:
                pass

    def _clean_pool(self):
        """Terminate the multiprocessing pool
        """
        if self._pool is not None:
            self._pool.terminate()
            self._pool = None
            self._map_func = None
            self._fitness_func = None

    def _stopping_criteria(self, population):
        """Verify whether the GA should stop or not
        Args:
            population (list): population of the current generation
        Returns:
            bool: True if algorithm should stop, False otherwise
        """
        return self.chromosome.stopping_criteria(population)

    def _gen_rand_individual(self):
        """Generate a random individual
        Returns:
            individual: a new random individual
        """
        return self.chromosome.gen_rand_individual()

    def _crossover(self, indiv_1, indiv_2, prob_1, prob_2):
        """Create individuals through crossover operation
        Args:
            indiv_1 (list): first individual
            indiv_2 (list): second individual
            prob_1 (float): value in [0, 1] is the probability of
                            an indiv_1 gene being chosen for the offspring
            prob_2 (float): value in [0, 1] is the probability of
                            an indiv_2 gene being chosen for the offspring
        Returns:
            list: list of offspring individuals
        """
        return self.chromosome.crossover(indiv_1, indiv_2, prob_1, prob_2)

    def _get_fitness(self, individual):
        """Calculate an individual fitness
        Args:
            individual (list): individual
        Returns:
            float: fitness value
        """
        # Check if the fitness is cached
        if len(individual) > self.nb_genes:
            return individual[-1]
        return self.chromosome.fitness(individual)

    def _get_fitnesses(self, population):
        """Calculate the fitness of all individuals in a population
        Args:
            population (list): population
        Returns:
            list: list of fitnesses of all individuals
        """
        fitnesses = list(self._map_func(self._fitness_func, population))
        # cache the fitness value inside the individual
        for (index, indiv) in enumerate(population):
            value = fitnesses[index]
            if len(indiv) == self.nb_genes:
                indiv.append(value)
        return fitnesses

    def _classify_population(self, population):
        """Sorts individuals by their fitness value
        Args:
            population (list): list of individuals
        Returns:
            list: list of sorted individuals
        """
        self._get_fitnesses(population)
        population.sort(key=lambda indiv: indiv[-1])
        return population

    def _gen_first_population(self, classify=True):
        """Generate the individuals of the first generation
        Args:
            classify (bool): whether the population should be classified according to their fitness
        """
        # Get bootstrap individuals generated by the chromosome representation
        pop = list(self.chromosome.gen_init_population())

        # Complete the population with random individuals
        rand_size = self.population_size - len(pop)
        if rand_size > 0:
            pop += [self._gen_rand_individual()
                    for i in range(rand_size)]

        if classify:
            return self._classify_population(pop)
        else:
            return pop

    def _gen_next_population(self, current_ranked_pop, classify=True):
        """Generate the next population
        through selection, crossover, mutation operations
        in the current population
        Args:
            current_ranked_pop (list): current sorted population
            classify (bool): whether the population should be classified according to their fitness
        Returns:
            list: list of individuals of the next population
        """
        next_population = []

        # Get elite individuals
        elite = current_ranked_pop[:self._elite_size]
        next_population += elite

        # Get mutant individuals
        mutants = [self._gen_rand_individual()
                   for _ in range(self._mutant_size)]
        next_population += mutants

        # Get individuals by crossover operation
        non_elite = current_ranked_pop[self._elite_size:]
        if self._elite_size == 0:
            elite = non_elite
        while len(next_population) < self.population_size:
            indiv_1 = random.choice(elite)
            indiv_2 = random.choice(non_elite)
            offspring = self._crossover(indiv_1, indiv_2,
                                        self.elite_probability,
                                        1.0 - self.elite_probability)
            next_population += offspring

        if classify:
            # Select individuals with best fitness for next generation
            next_population = self._classify_population(next_population)
            return next_population[:self.population_size]
        else:
            return next_population

    def solve(self):
        """Execute the genetic algorithm
        """
        self._init_params()
        pop = self._gen_first_population()
        try:
            for i in range(self.nb_generations):
                if self._stopping_criteria(pop):
                    break
                pop = self._gen_next_population(pop)
        except KeyboardInterrupt:
            raise
        finally:
            self._clean_pool()
            return pop


class BRKGAChromosome:
    """Abstract chromosome class
    It is used to implement the decoding algorithm of BRKGA
    for a specific problem
    """

    def __init__(self):
        """Object initialization
        """
        self.nb_genes = 1

    def init_params(self):
        """Initialize parameters before starting the genetic algorithm
        """
        pass

    def gen_rand_individual(self):
        """Generate a random individual
        Returns:
            individual: a new individual
        """
        return [random.random() for _ in range(self.nb_genes)]

    def gen_init_population(self):
        """Generate some individuals for the first population
        It is used to add bootstrap individual
        Returns:
            individuals: list of individuals
        """
        return []

    def crossover(self, indiv_1, indiv_2, prob_1, prob_2):
        """Execute the crossover operation
        Default: implement the Parameterized Uniform Crossover
        See also: https://doi.org/10.21236/ADA293985
        Args:
            indiv_1 (list): first individual
            indiv_2 (list): second individual
            prob_1 (float): value in [0, 1] is the probability of
                            an indiv_1 gene being chosen for the offspring
            prob_2 (float): value in [0, 1] is the probability of
                            an indiv_2 gene being chosen for the offspring
        Returns:
            list: list of offspring
        """
        if prob_1 < prob_2:
            indiv_1, indiv_2 = indiv_2, indiv_1
            prob_1, prob_2 = prob_2, prob_1

        offspring_1 = indiv_1[:self.nb_genes]
        offspring_2 = indiv_2[:self.nb_genes]

        for g in range(self.nb_genes):
            if random.random() > prob_1:
                offspring_1[g] = indiv_2[g]
                offspring_2[g] = indiv_1[g]

        return [offspring_1, offspring_2]

    def stopping_criteria(self, population):
        """Verify whether the GA should stop or not
        Args:
            population (list): population of the current generation
        Returns:
            bool: True if algorithm should stop, False otherwise
        """
        return False

    def fitness(self, individual):
        """Calculate the fitness of an individual
        Args:
            individual (list): individual
        Returns:
            float: fitness value
        """
        return 0.0
