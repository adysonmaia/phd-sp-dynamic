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
                 system_estimator,
                 dominance_func,
                 pool_size,
                 **ga_params):

        PlanFinder.__init__(self,
                            system=system,
                            environment_inputs=environment_inputs,
                            objective=objective,
                            objective_aggregator=objective_aggregator,
                            system_estimator=system_estimator,
                            dominance_func=dominance_func,
                            pool_size=pool_size)
        self.ga_params = ga_params

    def solve(self, control_inputs):
        ga_operator = GAPFOperator(control_inputs, self.sequence_length, self.create_plan)
        ga = NSGAII(operator=ga_operator,
                    pool_size=self.pool_size,
                    dominance_func=self.dominance_func,
                    **self.ga_params)
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
    def __init__(self, control_inputs, sequence_length, plan_creator):
        """Initialization
        Args:
            control_inputs (list): list of control inputs
            sequence_length (int): sequence's length
            plan_creator (function): function to create a plan
        """
        GAOperator.__init__(self)
        self.control_inputs = control_inputs
        self.sequence_length = sequence_length
        self.plan_creator = plan_creator

    @property
    def nb_genes(self):
        """Number of genes of the chromosome
        Returns:
            int: number of genes
        """
        return self.sequence_length

    def rand_individual(self):
        """Generate a random individual
        Returns:
            individual (GAIndividual): a new individual
        """
        chromosome = [0] * self.nb_genes
        inputs_length = len(self.control_inputs)
        for index in range(self.nb_genes):
            value = random.randrange(inputs_length)
            chromosome[index] = value
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
        control_sequence = [self.control_inputs[gene] for gene in individual]
        return control_sequence

