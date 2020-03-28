from sp.core.heuristic.nsgaii import NSGAII
from sp.core.heuristic.brkga import GAOperator, GAIndividual
from .plan_finder import PlanFinder, Plan
import random


class GAPlanFinder(PlanFinder):
    def __init__(self,
                 system,
                 environment_inputs,
                 objective,
                 objective_aggregator,
                 control_decoder,
                 system_estimator,
                 pool_size,
                 **ga_params):
        PlanFinder.__init__(self,
                            system=system,
                            environment_inputs=environment_inputs,
                            objective=objective,
                            objective_aggregator=objective_aggregator,
                            control_decoder=control_decoder,
                            system_estimator=system_estimator,
                            pool_size=pool_size)
        self.ga_params = ga_params

    def solve(self, control_inputs):
        ga_operator = GAPFOperator(stages=control_inputs, plan_creator=self.create_plan)
        ga = NSGAII(operator=ga_operator, pool_size=self.pool_size, **self.ga_params)
        population = ga.solve()

        plans = []
        for indiv in population:
            plan = None
            control_sequence = ga_operator.decode(indiv)
            if indiv.is_fitness_valid():
                plan = Plan(control_sequence=control_sequence, fitness=indiv.fitness)
            else:
                plan = self.create_plan(control_sequence)
            plans.append(plan)
        return plans


class GAPFOperator(GAOperator):
    """Genetic operator for GAPlanFinder
    """
    def __init__(self, stages, plan_creator):
        """Initialization
        Args:
            stages (list(list)): list of control inputs per stage
            plan_creator (function): function to create a plan
        """
        GAOperator.__init__(self)
        self.stages = stages
        self.plan_creator = plan_creator

    @property
    def nb_genes(self):
        """Number of genes of the chromosome
        Returns:
            int: number of genes
        """
        return len(self.stages)

    def rand_individual(self):
        """Generate a random individual
        Returns:
            individual (GAIndividual): a new individual
        """
        chromosome = [0] * self.nb_genes
        for stage in range(self.nb_genes):
            stage_size = len(self.stages[stage])
            value = random.randrange(stage_size)
            chromosome[stage] = value
        return GAIndividual(chromosome)

    def evaluate(self, individual):
        """Evaluate an individual and obtain its fitness
        Args:
            individual (GAIndividual): individual
        Returns:
            object: fitness value
        """
        control_sequence = self.decode(individual)
        plan = self.plan_creator(control_sequence)
        return plan.fitness

    def decode(self, individual):
        """Decode an individual's chromosome and obtain a sequence of control inputs
        Args:
            individual (GAIndividual): encoded individual
        Returns:
            list: sequence of control inputs
        """
        control_sequence = [self.stages[s][individual[s]] for s in range(self.nb_genes)]
        return control_sequence

