from .stage_ga import StageGA, StageGAOperator, preferred_dominates
from .plan_finder import GAPlanFinder, BeamPlanFinder, RandomPlanFinder
import math

_SGA_PARAMS = {
    "population_size": 100,
    "elite_proportion": 0.1,
    "mutant_proportion": 0.1,
    "elite_probability": 0.6,
    "pool_size": 0,
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
                 max_iterations=100,
                 system_estimator=None,
                 environment_predictor=None,
                 objective_aggregator=None,
                 dominance_func=preferred_dominates,
                 pool_size=0):

        self.max_iterations = max_iterations
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

    def solve(self):
        env_inputs = None
        if self.environment_predictor is not None and self.prediction_window > 0:
            env_inputs = [self.environment_input]
            env_inputs += self.environment_predictor.predict(self.prediction_window)
        else:
            env_inputs = [self.environment_input] * self.nb_stages

        stages_ga = []
        for stage in range(self.nb_stages):
            env_input = env_inputs[stage]
            ga_operator = StageGAOperator(system=self.system,
                                          environment_input=env_input,
                                          objective=self.objective,
                                          use_heuristic=True)
            ga = StageGA(operator=ga_operator,
                         nb_generations=self.max_iterations,
                         dominance_func=self.dominance_func,
                         **_SGA_PARAMS)
            ga.init_params()
            stages_ga.append(ga)
        first_stage_ga = stages_ga[0]

        # plan_finder = GAPlanFinder(system=self.system,
        #                            environment_inputs=env_inputs,
        #                            objective=self.objective,
        #                            objective_aggregator=self.objective_aggregator,
        #                            dominance_func=self.dominance_func,
        #                            control_decoder=_decode_control_input,
        #                            system_estimator=self.system_estimator,
        #                            pool_size=self.pool_size,
        #                            **_GAPF_PARAMS)

        # plan_finder = BeamPlanFinder(system=self.system,
        #                              environment_inputs=env_inputs,
        #                              objective=self.objective,
        #                              objective_aggregator=self.objective_aggregator,
        #                              dominance_func=self.dominance_func,
        #                              control_decoder=_decode_control_input,
        #                              system_estimator=self.system_estimator,
        #                              pool_size=self.pool_size,
        #                              **_BPF_PARAMS)

        plan_finder = RandomPlanFinder(system=self.system,
                                       environment_inputs=env_inputs,
                                       objective=self.objective,
                                       objective_aggregator=self.objective_aggregator,
                                       control_decoder=_decode_control_input,
                                       system_estimator=self.system_estimator,
                                       pool_size=self.pool_size,
                                       **_RPF_PARAMS)

        iteration = 0
        stop = False
        while not stop:
            stages_control = []
            for ga in stages_ga:
                if iteration > 0:
                    ga.next_population()
                else:
                    ga.first_population()
                stages_control.append(ga.current_population)

            population = first_stage_ga.current_population
            population = list(filter(lambda indiv: not indiv.is_fitness_valid(), population))
            if len(population) > 0:
                control_sequences = [[indiv] * self.nb_stages for indiv in population]
                plans = plan_finder.create_plans(control_sequences)
                for (indiv, plan) in zip(population, plans):
                    indiv.fitness = plan.fitness

            plans = []
            if self.nb_stages > 1:
                plans = plan_finder.solve(stages_control)
            for plan in plans:
                for stage in range(self.nb_stages):
                    control_input = plan[stage]
                    replace_fitness = False
                    if control_input.is_fitness_valid() and plan.is_fitness_valid():
                        replace_fitness = self.dominance_func(plan.fitness, control_input.fitness)
                    elif (not control_input.is_fitness_valid()) and plan.is_fitness_valid():
                        replace_fitness = True
                    if replace_fitness:
                        control_input.fitness = plan.fitness

            default_fitness = [math.inf for _ in self.objective]
            for ga in stages_ga:
                for indiv in ga.current_population:
                    if not indiv.is_fitness_valid():
                        indiv.fitness = default_fitness
                ga.select_individuals()

            iteration += 1
            stop = iteration >= self.max_iterations or first_stage_ga.should_stop()

        for ga in stages_ga:
            ga.clear_params()

        solution = first_stage_ga.current_population[0]
        # return _decode_control_input(self.system, solution, env_inputs[0])
        return first_stage_ga.operator.decode(solution)


def _decode_control_input(system, encoded_control, environment_input):
    ga_operator = StageGAOperator(system=system,
                                  environment_input=environment_input,
                                  objective=None,
                                  use_heuristic=False)
    return ga_operator.decode(encoded_control)
