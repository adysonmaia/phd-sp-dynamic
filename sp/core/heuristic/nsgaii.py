from functools import cmp_to_key
from sp.core.heuristic.brkga import BRKGA, GAIndividual, GAOperator

MAX_CRWD_DIST = 1.0


def pareto_dominates(fitness_1, fitness_2):
    """Check if the first individual dominates the second individual based on their fitness.
    It uses the classical Pareto dominance operator

    Args:
        fitness_1 (list): fitness of the first individual
        fitness_2 (list): fitness of the second individual
    Returns:
        bool: True if first individual dominates the second individual
    """
    dominates = False
    for i in range(len(fitness_1)):
        if fitness_1[i] > fitness_2[i]:
            return False
        elif fitness_1[i] < fitness_2[i]:
            dominates = True

    return dominates


class NSGAII(BRKGA):
    """Non-dominated Sorting Genetic Algorithm II

    See Also: https://doi.org/10.1109/4235.996017
    """

    def __init__(self,
                 dominance_func=pareto_dominates,
                 stop_threshold=0.0,
                 **brkga_params):
        """Initialization

        Args:
            dominance_func (function): dominance operator
            stop_threshold (float): MGBM stopping threshold. See Also: https://doi.org/10.1016/j.ins.2016.07.025
            **brkga_params: initialization parameters for :py:class:`sp.core.heuristic.brkga.BRKGA` algorithm
        """
        BRKGA.__init__(self, **brkga_params)
        self.stop_threshold = stop_threshold
        self.dominance_func = dominance_func

        # MGBM parameters
        self._previous_nd_fitness = None
        self._current_nd_fitness = None
        self._mgbm_estimation = 1
        self._mgbm_count = 0

    def init_params(self):
        """Initialize parameters before starting the genetic algorithm
        """
        BRKGA.init_params(self)
        self._previous_nd_fitness = None
        self._current_nd_fitness = None
        self._mgbm_estimation = 1
        self._mgbm_count = 0

    def should_stop(self, population):
        """Verify whether the GA should stop or not

        Args:
            population (list(GAIndividual)): population of the current generation
        Returns:
            bool: True if algorithm should stop, False otherwise
        """
        stop = self._should_stop_by_timeout()
        stop = stop or self.operator.should_stop(population)
        stop = stop or self._should_stop_by_mgbm()
        return stop

    def _should_stop_by_mgbm(self):
        """Calculate the MGBM stopping criteria based on Mutual Domination Rate (MDR) indicator 
        and a simplified Kalman filter.
        See Also: https://doi.org/10.1016/j.ins.2016.07.025
        
        Returns:
            bool: True if algorithm should stop according to the MGBM criteria, False otherwise
        """
        self._mgbm_count += 1
        if self._previous_nd_fitness:
            prev_fitnesses = self._previous_nd_fitness
            curr_fitnesses = self._current_nd_fitness

            prev_count = 0
            curr_count = 0
            for prev_fit in prev_fitnesses:
                for curr_fit in curr_fitnesses:
                    if self.dominance_func(curr_fit, prev_fit):
                        prev_count += 1
                        break

            for curr_fit in curr_fitnesses:
                for prev_fit in prev_fitnesses:
                    if self.dominance_func(prev_fit, curr_fit):
                        curr_count += 1
                        break

            mdr = (prev_count / float(len(prev_fitnesses))
                   - curr_count / float(len(curr_fitnesses)))

            t = self._mgbm_count
            i = self._mgbm_estimation
            i = (t / float(t + 1)) * i + (1 / float(t + 1)) * mdr
            self._mgbm_estimation = i

        return self._mgbm_estimation < self.stop_threshold

    def sort_population(self, population):
        """Sorts individuals using fast non dominated and crowding distance sorting algorithm

        Args:
            population (list(GAIndividual)): list of individuals
        Returns:
            list(GAIndividual): list of sorted individuals
        """
        fitnesses = self.evaluate_population(population)
        fronts, rank = fast_non_dominated_sort(fitnesses, self.dominance_func)
        crwd_dist = crowding_distance(fitnesses, fronts)

        self._previous_nd_fitness = self._current_nd_fitness
        self._current_nd_fitness = list(map(lambda i: fitnesses[i], fronts[0]))

        def sort_cmp(indiv_1, indiv_2):
            index_1 = population.index(indiv_1)
            index_2 = population.index(indiv_2)
            if rank[index_1] < rank[index_2]:
                return -1
            elif (rank[index_1] == rank[index_2]
                  and crwd_dist[index_1] < crwd_dist[index_2]):
                return -1
            else:
                return 1

        return sorted(population, key=cmp_to_key(sort_cmp))


def fast_non_dominated_sort(fitnesses, dominance_func=pareto_dominates):
    """Fast non-dominated sorting algorithm

    Args:
        fitnesses (list): fitness of each individual in a population
        dominance_func (function): dominance operator function
    Returns:
        (list, list): fronts, rank
    """
    pop_size = len(fitnesses)
    r_pop_size = list(range(pop_size))
    S = [[] for _ in r_pop_size]
    n = [0 for _ in r_pop_size]
    rank = [0 for _ in r_pop_size]
    fronts = [[]]

    test = [[] for _ in r_pop_size]

    for p in r_pop_size:
        S[p] = []
        n[p] = 0
        for q in r_pop_size:
            if dominance_func(fitnesses[p], fitnesses[q]):
                if q not in S[p]:
                    S[p].append(q)
            elif dominance_func(fitnesses[q], fitnesses[p]):
                n[p] = n[p] + 1
                if q not in test[p]:
                    test[p].append(q)
        if n[p] == 0:
            rank[p] = 0
            if p not in fronts[0]:
                fronts[0].append(p)

    i = 0
    while len(fronts[i]) > 0:
        Q = []
        for p in fronts[i]:
            for q in S[p]:
                n[q] = n[q] - 1
                if n[q] == 0:
                    rank[q] = i + 1
                    if q not in Q:
                        Q.append(q)
        i = i + 1
        fronts.append(Q)

    del fronts[len(fronts) - 1]
    return fronts, rank


def crowding_distance(fitnesses, fronts):
    """Crowding Distance

    Args:
        fitnesses (list): fitness of each individual in a population
        fronts (list(list)): front of each individual in a population.
            The fronts are obtained by fast non dominated sorting algorithm
    Returns:
        list: crowding distance of each individual
    """
    nb_obj = len(fitnesses[0])
    distances = [0.0 for _ in range(len(fitnesses))]

    normalize = []
    for m in range(nb_obj):
        values = [value[m] for value in fitnesses]
        min_value = min(values)
        max_value = max(values)
        normalize.append(float(max_value - min_value))

    for front in fronts:
        for m in range(nb_obj):
            s_front = list(front)
            s_front.sort(key=lambda p: fitnesses[p][m])
            distances[s_front[0]] = distances[s_front[-1]] = MAX_CRWD_DIST

            if normalize[m] > 0.0:
                for i in range(1, len(s_front) - 1):
                    value_previous = fitnesses[s_front[i - 1]][m]
                    value_next = fitnesses[s_front[i + 1]][m]
                    value_diff = value_next - value_previous
                    distances[s_front[i]] += value_diff / normalize[m]

    return distances
