from .stage_ga import StageGA, StageGAOperator, preferred_dominates, indiv_gen
from .plan_finder import GAPlanFinder, BeamPlanFinder, RandomPlanFinder
import copy

_SGA_PARAMS = {
    "nb_generations": 100,
    "population_size": 100,
    "elite_proportion": 0.1,
    "mutant_proportion": 0.1,
    "elite_probability": 0.6,
    "stop_threshold": 0.10,
}
_GAPF_PARAMS = {
    "nb_generations": 100,
    "population_size": 100,
    "elite_proportion": 0.1,
    "mutant_proportion": 0.1,
    "elite_probability": 0.6,
    "stop_threshold": 0.10,
}
_BPF_PARAMS = {
    "beam_width": 10,
    "prune": True,
}
_RPF_PARAMS = {
    "nb_plans": 100
}


class MultiStage:
    def __init__(self,
                 system,
                 environment_input,
                 objective,
                 prediction_window=1,
                 use_heuristic=True,
                 system_estimator=None,
                 environment_predictor=None,
                 objective_aggregator=None,
                 dominance_func=preferred_dominates,
                 pool_size=0):

        self.use_heuristic = use_heuristic
        self.prediction_window = prediction_window
        self.nb_stages = 1 + prediction_window
        self.system = system
        self.system_estimator = system_estimator
        self.environment_input = environment_input
        self.environment_predictor = environment_predictor
        self.objective = objective
        self.objective_aggregator = objective_aggregator
        self.dominance_func = dominance_func
        self.pool_size = pool_size

        self._env_inputs = None

    def __del__(self):
        """Finalizer
        """
        try:
            self.clear_params()
        except AttributeError:
            pass

    def clear_params(self):
        self._env_inputs = None

    def init_params(self):
        self._env_inputs = []
        if self.environment_predictor is not None and self.prediction_window > 0:
            self._env_inputs = [self.environment_input]
            self._env_inputs += self.environment_predictor.predict(self.prediction_window)
        else:
            self._env_inputs = [self.environment_input] * self.nb_stages

    def solve(self):
        self.init_params()
        stages_population = self._solve_part_1()
        solution = self._solve_part_2(stages_population)
        self.clear_params()
        return solution

    def _solve_part_1(self):
        stages_population = []
        for stage in range(self.nb_stages):
            env_input = self._env_inputs[stage]
            ga_operator = StageGAOperator(system=self.system,
                                          environment_input=env_input,
                                          objective=self.objective,
                                          use_heuristic=True)
            ga = StageGA(operator=ga_operator,
                         dominance_func=self.dominance_func,
                         pool_size=self.pool_size,
                         **_SGA_PARAMS)
            population = ga.solve()
            stages_population.append(population)
        return stages_population

    def _solve_part_2(self, stages_population):
        first_stage = 0
        first_ga_operator = StageGAOperator(system=self.system,
                                            environment_input=self._env_inputs[first_stage],
                                            objective=self.objective,
                                            use_heuristic=True)
        first_stage_ga = StageGA(operator=first_ga_operator,
                                 dominance_func=self.dominance_func,
                                 pool_size=0,
                                 **_SGA_PARAMS)
        first_stage_ga.init_params()
        first_stage_ga.current_population = stages_population[first_stage]

        plan_finder = GAPlanFinder(system=self.system,
                                   environment_inputs=self._env_inputs,
                                   objective=self.objective,
                                   objective_aggregator=self.objective_aggregator,
                                   dominance_func=self.dominance_func,
                                   control_decoder=_decode_control_input,
                                   system_estimator=self.system_estimator,
                                   pool_size=self.pool_size,
                                   **_GAPF_PARAMS)

        if self.nb_stages > 1:
            all_control_inputs = []
            for population in stages_population:
                all_control_inputs += population
            stages_population = [all_control_inputs] * self.nb_stages
            plans = plan_finder.solve(stages_population)

            if self.use_heuristic:
                control_sequences = []
                for indiv in all_control_inputs:
                    indiv = copy.copy(indiv)
                    sequence = [indiv] * self.nb_stages
                    control_sequences.append(sequence)
                for plan in plans:
                    indiv = indiv_gen.merge_population(first_ga_operator, plan.control_sequence)
                    sequence = [indiv] * self.nb_stages
                    control_sequences.append(sequence)
                plans += plan_finder.create_plans(control_sequences)

            population = []
            for plan in plans:
                control_input = plan[first_stage]
                control_input.fitness = plan.fitness
                population.append(control_input)
            first_stage_ga.current_population = population
            if len(population) > 1:
                first_stage_ga.select_individuals()

        solution = first_stage_ga.current_population[0]
        solution = first_ga_operator.decode(solution)

        first_stage_ga.clear_params()
        plan_finder.clear_params()

        return solution


def _decode_control_input(system, encoded_control, environment_input):
    ga_operator = StageGAOperator(system=system,
                                  environment_input=environment_input,
                                  objective=None,
                                  use_heuristic=False)
    return ga_operator.decode(encoded_control)
