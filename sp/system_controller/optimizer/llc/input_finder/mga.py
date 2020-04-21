from .input_finder import InputFinder
from sp.core.heuristic.nsgaii import NSGAII
from sp.system_controller.optimizer.moga import MOGAOperator
from multiprocessing.dummy import Pool as ThreadPool
import multiprocessing as mp


class MGAInputFinder(InputFinder):
    """Multi GAs Input Finder
    """

    def __init__(self,
                 system,
                 environment_inputs,
                 objective,
                 objective_aggregator,
                 system_estimator,
                 dominance_func,
                 pool_size,
                 last_inputs,
                 **ga_params):

        InputFinder.__init__(self,
                             system=system,
                             environment_inputs=environment_inputs,
                             objective=objective,
                             objective_aggregator=objective_aggregator,
                             system_estimator=system_estimator,
                             dominance_func=dominance_func,
                             pool_size=pool_size,
                             last_inputs=last_inputs)
        self.ga_params = ga_params

    def solve(self):
        map_func = map
        pool_size = int(min(self.pool_size, self.nb_slots, mp.cpu_count()))
        pool = None
        if pool_size > 1:
            try:
                pool = ThreadPool(self.pool_size)
                map_func = pool.map
            except ValueError:
                pass

        map_results = list(map_func(self._exec_ga, range(self.nb_slots)))
        population = []
        for pop in map_results:
            population += pop

        if pool is not None:
            pool.terminate()

        return population

    def _exec_ga(self, index):
        env_input = self.environment_inputs[index]
        ga_operator = MOGAOperator(system=self.system,
                                   environment_input=env_input,
                                   objective=self.objective,
                                   use_heuristic=True,
                                   first_population=self.last_inputs)
        ga = NSGAII(operator=ga_operator,
                    dominance_func=self.dominance_func,
                    pool_size=self.pool_size,
                    **self.ga_params)
        population = ga.solve()
        return population
