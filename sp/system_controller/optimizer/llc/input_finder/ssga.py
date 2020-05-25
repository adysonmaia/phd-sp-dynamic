from .input_finder import InputFinder
from ..plan_finder import PlanFinder, EmptyPlanFinder
from sp.core.heuristic.nsgaii import NSGAII
from sp.system_controller.optimizer.moga import MOGAOperator


class SSGAInputFinder(InputFinder):
    """Simple Sequence GA Input Finder

    It is a genetic algorithm that generates sequences of control inputs.
    A sequence is composed of the same control input

    Attributes:
        ga_params (dict): initialization parameters of :py:class:`~sp.core.heuristic.nsgaii.NSGAII` class
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
        """Initialization
        """

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
        self._plan_finder = EmptyPlanFinder(system=system,
                                            environment_inputs=environment_inputs,
                                            objective=objective,
                                            objective_aggregator=objective_aggregator,
                                            system_estimator=system_estimator,
                                            dominance_func=dominance_func,
                                            pool_size=pool_size)

    def solve(self):
        """Execute the heuristic

        Returns:
            list(GAIndividual): list of encoded control inputs
        """

        ga_operator = SSGAOperator(plan_finder=self._plan_finder,
                                   sequence_length=self.nb_slots,
                                   use_heuristic=True,
                                   extra_first_population=self.last_inputs)
        ga = NSGAII(operator=ga_operator,
                    dominance_func=self.dominance_func,
                    pool_size=self.pool_size,
                    **self.ga_params)
        population = ga.solve()
        return population


class SSGAOperator(MOGAOperator):
    """Simple Sequence GA Operator

    Attributes:
        plan_finder (PlanFinder): plan finder
        sequence_length (int): sequence length
    """

    def __init__(self, plan_finder, sequence_length, use_heuristic=True, extra_first_population=None):
        """Initialization

        Args:
            plan_finder (PlanFinder): plan finder
            sequence_length (int): sequence length
            use_heuristic (bool): use heuristic algorithms to generate the first population
            extra_first_population (list(GAIndividual)): list of individuals to be added in the first population
        """
        env_input = plan_finder.environment_inputs[0]
        MOGAOperator.__init__(self,
                              objective=plan_finder.objective,
                              system=plan_finder.system,
                              environment_input=env_input,
                              use_heuristic=use_heuristic,
                              extra_first_population=extra_first_population)

        self.plan_finder = plan_finder
        self.sequence_length = sequence_length

    def evaluate(self, individual):
        """Evaluate an individual and obtain its fitness

        Args:
            individual (GAIndividual): individual
        Returns:
            object: fitness value
        """
        sequence = [individual] * self.sequence_length
        plan = self.plan_finder.create_plan(sequence)
        return plan.fitness
