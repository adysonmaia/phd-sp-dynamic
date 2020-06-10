from sp.core.heuristic.nsgaii import NSGAII
from sp.system_controller.optimizer.moga import MOGAOptimizer, MOGAOperator
from sp.system_controller.model import OptSolution


class OmittedMigrationOptimizer(MOGAOptimizer):
    """Omitted Migration Optimizer
    """

    def solve(self, system, environment_input):
        """Solve the service placement problem

        Args:
            system (sp.core.model.system.System): current system's state
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        Returns:
            sp.system_controller.model.opt_solution.OptSolution: problem solution
        """
        self.init_params()
        ga_operator = OmittedMigrationGAOperator(objective=self.objective,
                                                 system=system,
                                                 environment_input=environment_input,
                                                 use_heuristic=self.use_heuristic,
                                                 extra_first_population=self._last_population)
        mo_ga = NSGAII(operator=ga_operator,
                       nb_generations=self.nb_generations,
                       population_size=self.population_size,
                       elite_proportion=self.elite_proportion,
                       mutant_proportion=self.mutant_proportion,
                       elite_probability=self.elite_probability,
                       stop_threshold=self.stop_threshold,
                       dominance_func=self.dominance_func,
                       timeout=self.timeout,
                       pool_size=self.pool_size)
        population = mo_ga.solve()

        self._last_population = population
        solution = ga_operator.decode(population[0])
        return solution


class OmittedMigrationGAOperator(MOGAOperator):
    """Omitted Migration GA Operator
    """

    def _calc_response_time(self, app, src_node, dst_node, solution, cached_delays):
        """Calculate response time of requests from src_node to dst_node

        Args:
            app (sp.core.model.application.Application): requested application
            src_node (sp.core.model.node.Node): source node
            dst_node (sp.core.model.node.Node): destination node
            solution (OptSolution): solution
            cached_delays (sp.system_controller.optimizer.soga.ga_operator._CachedDelays): cached delays
        Returns:
            float: response time
        """
        init_delay = 0.0
        cached_delays.set_init_delay(app.id, dst_node.id, init_delay)
        MOGAOperator._calc_response_time(self, app, src_node, dst_node, solution, cached_delays)
        cached_delays.set_init_delay(app.id, dst_node.id, init_delay)
        return cached_delays.get_rt(app.id, src_node.id, dst_node.id)

