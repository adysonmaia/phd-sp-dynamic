from .stage_ga import StageGA, StageChromosome
from .plan_finder.ga import GAPlanFinder
from .plan_finder.beam import BeamPlanFinder
import time

INF = float("inf")
_SGA_PARAMS = {
    "population_size": 100,
    "elite_proportion": 0.1,
    "mutant_proportion": 0.1,
    "elite_probability": 0.6,
    "dominance_tolerance": 0.01,
    "pool_size": 0,
    "stop_threshold": 0.10,
    "use_heuristic": True
}
_GAPF_PARAMS = {
    "nb_generations": 100,
    "population_size": 100,
    "elite_proportion": 0.1,
    "mutant_proportion": 0.1,
    "elite_probability": 0.6,
    "dominance_tolerance": 0.01,
    "pool_size": 6,
    "stop_threshold": 0.10,
}
_BPF_PARAMS = {
    "beam_width": 10,
    "prune": True,
    "pool_size": 6
}


class MultiStage:
    def __init__(self,
                 system,
                 environment_input,
                 objective,
                 nb_stages=1,
                 max_iterations=10,
                 system_estimator=None,
                 environment_predictor=None,
                 objective_aggregator=None):

        self.max_iterations = max_iterations
        self.nb_stages = nb_stages
        self.system = system
        self.system_estimator = system_estimator
        self.environment_input = environment_input
        self.environment_predictor = environment_predictor
        self.objective = objective
        self.objective_aggregator = objective_aggregator

    def solve(self):
        env_inputs = None
        if self.environment_predictor is not None and self.nb_stages > 1:
            env_inputs = [self.environment_input]
            env_inputs += self.environment_predictor.predict(self.nb_stages - 1)
        else:
            env_inputs = [self.environment_input] * self.nb_stages

        stages_ga = []
        for stage in range(self.nb_stages):
            env_input = env_inputs[stage]
            ga = StageGA(system=self.system,
                         environment_input=env_input,
                         objective=self.objective,
                         nb_generations=self.max_iterations,
                         **_SGA_PARAMS)
            stages_ga.append(ga)

        plan_finder = GAPlanFinder(system=self.system,
                                   environment_inputs=env_inputs,
                                   objective=self.objective,
                                   objective_aggregator=self.objective_aggregator,
                                   control_decoder=_decode_control_input,
                                   system_estimator=self.system_estimator,
                                   ga_params=_GAPF_PARAMS)

        # plan_finder = BeamPlanFinder(system=self.system,
        #                              environment_inputs=env_inputs,
        #                              objective=self.objective,
        #                              objective_aggregator=self.objective_aggregator,
        #                              control_decoder=_decode_control_input,
        #                              system_estimator=self.system_estimator,
        #                              **_BPF_PARAMS)

        iteration = 0
        stop = False
        while not stop:
            stages_control = []
            for stage in range(self.nb_stages):
                ga = stages_ga[stage]
                population = ga.next_population()

                for indiv in population:
                    fitness = None

                    if stage > 0:
                        fitness = [INF] * len(self.objective)
                    else:
                        trajectory = [indiv] * self.nb_stages
                        plan = plan_finder.create_plan(trajectory)
                        fitness = plan.fitness

                    ga.set_fitness(indiv, fitness)
                stages_control.append(population)

            plans = plan_finder.solve(stages_control)
            for plan in plans:
                for stage in range(self.nb_stages):
                    control_input = plan[stage]
                    ga = stages_ga[stage]
                    fitness = ga.get_fitness(control_input)

                    # TODO: improve the code below
                    if ga.dominates(plan.fitness, fitness):
                        ga.set_fitness(control_input, plan.fitness)

            iteration += 1
            stop = (iteration >= self.max_iterations) or stages_ga[0].is_stopping_criteria_met()

        solution = stages_ga[0].current_population[0]
        return _decode_control_input(self.system, solution, env_inputs[0])


def _decode_control_input(system, encoded_control, environment_input):
    chromosome = StageChromosome(system=system, environment_input=environment_input)
    return chromosome.decode(encoded_control)
