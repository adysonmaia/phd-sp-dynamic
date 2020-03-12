from sp.core.heuristic.nsgaii import NSGAIIChromosome
from sp.system_controller.optimizer.static.moga import MOGA
from . import PlanFinder
import random


class GAPlanFinder(PlanFinder):
    def __init__(self,
                 system,
                 environment_inputs,
                 objective,
                 objective_aggregator,
                 control_decoder,
                 system_estimator,
                 ga_params):
        PlanFinder.__init__(self,
                            system=system,
                            environment_inputs=environment_inputs,
                            objective=objective,
                            objective_aggregator=objective_aggregator,
                            control_decoder=control_decoder,
                            system_estimator=system_estimator)
        self.ga_params = ga_params

    def solve(self, control_inputs):
        chromosome = PFChromosome(stages=control_inputs, plan_creator=self.create_plan)
        ga = MOGA(chromosome=chromosome, **self.ga_params)
        population = ga.solve()
        # TODO: cache this decoding in the GA algorithm
        plans = [chromosome.decode(indiv) for indiv in population]
        return plans


class PFChromosome(NSGAIIChromosome):
    def __init__(self, stages, plan_creator):
        NSGAIIChromosome.__init__(self)
        self.stages = stages
        self.nb_genes = len(self.stages)
        self.plan_creator = plan_creator

    def gen_rand_individual(self):
        indiv = [0] * self.nb_genes
        for stage in range(self.nb_genes):
            stage_size = len(self.stages[stage])
            value = random.randrange(stage_size)
            indiv[stage] = value
        return indiv

    def fitness(self, individual):
        plan = self.decode(individual)
        return plan.fitness

    def decode(self, individual):
        control_sequence = [self.stages[s][individual[s]] for s in range(self.nb_genes)]
        return self.plan_creator(control_sequence)

