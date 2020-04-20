from sp.core.heuristic.nsgaii import NSGAII
from sp.system_controller.optimizer.optimizer import Optimizer
from sp.system_controller.metric import deadline, availability, cost
from .ga_operator import MOGAOperator, preferred_dominates


class MOGAOptimizer(Optimizer):
    def __init__(self):
        Optimizer.__init__(self)
        self.objective = None
        self.nb_generations = 100
        self.population_size = 100
        self.elite_proportion = 0.1
        self.mutant_proportion = 0.1
        self.elite_probability = 0.6
        self.dominance_func = preferred_dominates
        self.stop_threshold = 0.10
        self.use_heuristic = True
        self.pool_size = 4

        self._last_population = None

    def init_params(self):
        if self.objective is None:
            self.objective = [
                deadline.max_deadline_violation,
                cost.overall_cost,
                availability.avg_unavailability,
            ]

        if not isinstance(self.objective, list):
            self.objective = [self.objective]

    def clear_params(self):
        self._last_population = None

    def solve(self, system, environment_input):
        self.init_params()
        ga_operator = MOGAOperator(objective=self.objective,
                                   system=system,
                                   environment_input=environment_input,
                                   use_heuristic=self.use_heuristic,
                                   first_population=self._last_population)
        mo_ga = NSGAII(operator=ga_operator,
                       nb_generations=self.nb_generations,
                       population_size=self.population_size,
                       elite_proportion=self.elite_proportion,
                       mutant_proportion=self.mutant_proportion,
                       elite_probability=self.elite_probability,
                       stop_threshold=self.stop_threshold,
                       dominance_func=self.dominance_func,
                       pool_size=self.pool_size)
        population = mo_ga.solve()

        # if system.time >= 1211634000:
        #     list_indiv = [population[0]]
        #     if self._last_indiv is not None:
        #         list_indiv.append(self._last_indiv)
        #     for (index, indiv) in enumerate(list_indiv):
        #         fitness = ga_operator.evaluate(indiv)
        #         print('{} - fit {}'.format(index, fitness))
        #         control_input = ga_operator.decode(indiv)
        #         for app in system.apps:
        #             places = [n.id for n in system.nodes if control_input.get_app_placement(app.id, n.id)]
        #             print('\tapp {} - {}: {}'.format(app.id, len(places), places))

        self._last_population = population
        solution = ga_operator.decode(population[0])
        return solution