import random
from collections import UserList
from abc import ABC, abstractmethod
import multiprocessing as mp


_brkga = None


def _init_pool(genetic_algo):
    """Initialize a sub-process to calculate an individual fitness
    Args:
        genetic_algo (BRKGA): a genetic algorithm object
    """
    global _brkga
    _brkga = genetic_algo


def _evaluate(indiv):
    """Evaluate an individual and obtain its fitness
    Args:
        indiv (GAIndividual): individual
    Returns:
        object: fitness value
    """
    global _brkga
    return _brkga.evaluate(indiv)


class BRKGA:
    """ Biased Random Key Genetic Algorithm
    See also:
    https://link.springer.com/article/10.1007/s10732-010-9143-1
    """

    def __init__(self,
                 operator,
                 population_size,
                 nb_generations,
                 elite_proportion,
                 mutant_proportion,
                 elite_probability=None,
                 pool_size=0):
        """Initialize method
        Args:
            operator (GAOperator): genetic operator
            population_size (int): population size
            nb_generations (int): maximum number of generations
            elite_proportion (float): proportion of the number of elite individuals in the population, value in [0, 1]
            mutant_proportion (float): proportion of the number of mutant individuals in the population, value in [0, 1]
            elite_probability (float): probability of a elite gene to be selected during crossover
            pool_size (int): number of processes for parallelisms
        """

        self.operator = operator
        self.population_size = population_size
        self.nb_generations = nb_generations
        self.elite_proportion = elite_proportion
        self.mutant_proportion = mutant_proportion
        self.elite_probability = elite_probability

        self._elite_size = int(round(self.elite_proportion * self.population_size))
        self._mutant_size = int(round(self.mutant_proportion * self.population_size))

        if self.elite_probability is None:
            self.elite_probability = self._elite_size / float(self.population_size)

        self.current_population = list()

        self.pool_size = pool_size
        self._pool = None
        self._map_func = None
        self._evaluate_func = None

    def __del__(self):
        """Finalizer
        """
        try:
            self.clear_params()
        except AttributeError:
            pass

    def init_params(self):
        """Initialize parameters before starting the genetic algorithm
        """
        self._elite_size = int(round(self.elite_proportion * self.population_size))
        self._mutant_size = int(round(self.mutant_proportion * self.population_size))
        self._init_pool()
        self.current_population = list()
        self.operator.init_params()

    def clear_params(self):
        """Clear parameters after the execution of the genetic algorithm
        """
        self._clear_pool()

    def _init_pool(self):
        """Initialize the multiprocessing pool
        """
        self._clear_pool()

        self._pool = None
        self._map_func = map
        self._evaluate_func = self.evaluate
        if self.pool_size > 0:
            try:
                # Require UNIX fork to work
                mp_ctx = mp.get_context("fork")
                self.pool_size = min(self.pool_size, mp_ctx.cpu_count())
                self._pool = mp_ctx.Pool(processes=self.pool_size,
                                         initializer=_init_pool,
                                         initargs=[self])
                self._map_func = self._pool.map
                self._evaluate_func = _evaluate
            except ValueError:
                pass

    def _clear_pool(self):
        """Terminate the multiprocessing pool
        """
        if self._pool is not None:
            self._pool.terminate()
            self._pool = None
            self._map_func = None
            self._evaluate_func = None

    def should_stop(self, population):
        """Verify whether the GA should stop or not
        Args:
            population (list(GAIndividual)): population of the current generation
        Returns:
            bool: True if algorithm should stop, False otherwise
        """
        return self.operator.should_stop(population)

    def rand_individual(self):
        """Generate a random individual
        Returns:
            GAIndividual: a new random individual
        """
        return self.operator.rand_individual()

    def first_population(self, apply_selection=True):
        """Generate the individuals of the first generation
        Args:
            apply_selection (bool): if the selection operation will be applied for the generated individuals
        Returns:
            list(GAIndividual): list of sorted individuals
        """
        # Get initial individuals of the operator
        pop = list(self.operator.first_population())

        # Complete the population with random individuals
        rand_size = self.population_size - len(pop)
        if rand_size > 0:
            pop += [self.rand_individual() for _ in range(rand_size)]

        # Apply selection operation if necessary
        if apply_selection:
            pop = self.select_individuals(pop)

        return pop

    def evaluate(self, individual):
        """Evaluate an individual and obtain its fitness
        Args:
            individual (GAIndividual): individual
        Returns:
            object: fitness value
        """
        if individual.is_fitness_valid():
            return individual.fitness
        else:
            fitness = self.operator.evaluate(individual)
            individual.fitness = fitness
            return fitness

    def evaluate_population(self, population):
        """Calculate the fitness of all individuals in a population
        Args:
            population (list(GAIndividual)): population
        Returns:
            list: list of fitness
        """
        fitnesses = list(self._map_func(self._evaluate_func, population))
        for (fitness, indiv) in zip(fitnesses, population):
            indiv.fitness = fitness
        return fitnesses

    def sort_population(self, population):
        """Sorts individuals by their fitness value
        Args:
            population (list(GAIndividual)): list of individuals
        Returns:
            list(GAIndividual): list of sorted individuals
        """
        self.evaluate_population(population)
        population.sort(key=lambda individual: individual.fitness)
        return population

    def select_individuals(self, population):
        """Select best individuals in a population
        Args:
            population (list(GAIndividual)): list of individuals
        Returns:
            list(GAIndividual): selected individuals
        """
        population = self.sort_population(population)
        return population[:self.population_size]

    def crossover(self, indiv_1, indiv_2, prob_1, prob_2):
        """Create individuals through crossover operation
        Args:
            indiv_1 (GAIndividual): first individual
            indiv_2 (GAIndividual): second individual
            prob_1 (float): value in [0, 1] is the probability of an indiv_1 gene being chosen for the offspring
            prob_2 (float): value in [0, 1] is the probability of an indiv_2 gene being chosen for the offspring
        Returns:
            list: list of offspring individuals
        """
        return self.operator.crossover(indiv_1, indiv_2, prob_1, prob_2)

    def next_population(self, population, apply_selection=True):
        """Generate the next population through crossover and mutation operations in the current population
        Args:
            population (list): sorted population
            apply_selection (bool): if the selection operation will be applied in the next population
        Returns:
            list: list of individuals of the next population
        """
        next_population = []

        # Get elite individuals
        elite = population[:self._elite_size]
        next_population += elite

        # Get mutant individuals
        mutants = [self.rand_individual() for _ in range(self._mutant_size)]
        next_population += mutants

        # Get individuals by crossover operation
        non_elite = population[self._elite_size:]
        if self._elite_size == 0:
            elite = non_elite
        while len(next_population) < self.population_size:
            indiv_1 = random.choice(elite)
            indiv_2 = random.choice(non_elite)
            offspring = self.crossover(indiv_1, indiv_2,
                                       self.elite_probability,
                                       1.0 - self.elite_probability)
            next_population += offspring

        # Apply selection operation if necessary
        if apply_selection:
            next_population = self.select_individuals(next_population)

        return next_population

    def solve(self):
        """Execute the genetic algorithm
        Returns:
            list(GAIndividual): list of best individuals found
        """
        self.init_params()
        self.current_population = self.first_population(apply_selection=True)
        try:
            for _ in range(self.nb_generations):
                if self.should_stop(self.current_population):
                    break
                self.current_population = self.next_population(self.current_population, apply_selection=True)
        except KeyboardInterrupt:
            raise
        finally:
            self.clear_params()
            return self.current_population


class GAIndividual(UserList):
    """Individual of a genetic algorithm
    """
    def __init__(self, chromosome=None):
        """Initialization
        Args:
            chromosome (list): chromosome's data
        """
        UserList.__init__(self, chromosome)
        self.fitness = None

    def is_fitness_valid(self):
        """Check if the individual's is valid
        Returns:
            bool: True if the fitness is valid, False otherwise
        """
        return self.fitness is not None

    def clear_copy(self):
        """Copy individual with invalid fitness
        Returns:
            GAIndividual: copy
        """
        indiv = GAIndividual(self.data)
        indiv.fitness = None
        return indiv

    @property
    def nb_genes(self):
        """ Number of genes of the chromosome
        Returns:
            int: number of genes
        """
        return len(self.data)

    @property
    def chromosome(self):
        """Individual's chromosome
        Returns:
            list: chromosome data
        """
        return self.data


class GAOperator(ABC):
    """Abstract chromosome class
       It is used to implement the decoding algorithm of BRKGA
       for a specific problem
       """

    def __init__(self):
        """Initialization
        """
        ABC.__init__(self)

    @property
    @abstractmethod
    def nb_genes(self):
        """Number of genes in the chromosome
        Returns:
            int: number of genes in a individual's chromosome
        """
        pass

    def init_params(self):
        """Initialize parameters before starting the genetic algorithm
        """
        pass

    def rand_individual(self):
        """Generate a random individual
        Returns:
            individual (GAIndividual): a new individual
        """
        data = [random.random() for _ in range(self.nb_genes)]
        return GAIndividual(data)

    def first_population(self):
        """Generate some individuals for the first population
        It is used to add bootstrap individual
        Returns:
            individuals (list(GAIndividual)): list of individuals
        """
        return []

    def crossover(self, indiv_1, indiv_2, prob_1, prob_2):
        """Execute the crossover operation
        Default: implement the Parameterized Uniform Crossover
        See also: https://doi.org/10.21236/ADA293985
        Args:
            indiv_1 (GAIndividual): first individual
            indiv_2 (GAIndividual): second individual
            prob_1 (float): value in [0, 1] is the probability of an indiv_1 gene being chosen for the offspring
            prob_2 (float): value in [0, 1] is the probability of an indiv_2 gene being chosen for the offspring
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

        return [GAIndividual(offspring_1), GAIndividual(offspring_2)]

    def should_stop(self, population):
        """Verify whether the GA should stop or not
        Args:
            population (list(GAIndividual)): population of the current generation
        Returns:
            bool: True if genetic algorithm should stop, False otherwise
        """
        return False

    @abstractmethod
    def evaluate(self, individual):
        """Evaluate an individual and obtain its fitness
        Args:
            individual (GAIndividual): individual
        Returns:
            object: fitness value
        """
        pass
