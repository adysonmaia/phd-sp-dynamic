from sp.core.heuristic.nsgaii import NSGAII
from sp.system_controller.optimizer.moga import MOGAOptimizer, MOGAOperator
from sp.system_controller.model import OptSolution


class NoMigrationOptimizer(MOGAOptimizer):
    """No Migration Optimizer
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
        ga_operator = NoMigrationGAOperator(objective=self.objective,
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


class NoMigrationGAOperator(MOGAOperator):
    """No Migration GA Operator
    """

    def _decode_part_1(self, individual):
        """Decode Part I.
        It selects candidate nodes to host applications

        Args:
            individual (GAIndividual): individual
        Returns:
            (OptSolution, dict): solution, list of selected nodes per application
        """
        prev_control_input = self.system.control_input
        cloud_node = self.system.cloud_node
        selected_nodes = None
        solution = None
        if prev_control_input is None:
            solution, selected_nodes = MOGAOperator._decode_part_1(self, individual)
        else:
            solution = OptSolution.create_empty(self.system)
            selected_nodes = {}
            for app in self.system.apps:
                app_nodes = []
                for node in self.system.nodes:
                    if prev_control_input.get_app_placement(app.id, node.id):
                        app_nodes.append(node)
                selected_nodes[app.id] = app_nodes

        for app in self.system.apps:
            app_nodes = selected_nodes[app.id]
            if cloud_node not in app_nodes:
                app_nodes.append(cloud_node)

        return solution, selected_nodes

    def _decode_part_2(self, individual, solution, selected_nodes):
        """Decode Part II.
        It distributes load among the selected nodes of part I

        Args:
            individual (GAIndividual): individual
            solution (OptSolution): solution
            selected_nodes (dict): selected nodes of part I
        Returns:
            OptSolution: solution
        """
        prev_control_input = self.system.control_input
        if prev_control_input is not None:
            for app in self.system.apps:
                for node in selected_nodes[app.id]:
                    if self._alloc_resources(app, node, solution, load=0.0, increment=False):
                        solution.app_placement[app.id][node.id] = True
        return MOGAOperator._decode_part_2(self, individual, solution, selected_nodes)

    def _decode_part_3(self, individual, solution, selected_nodes):
        """Decode Part III.
        It is a local search to make solution feasible

        Args:
            individual (GAIndividual): individual
            solution (OptSolution): solution
            selected_nodes (dict): selected nodes of part I
        Returns:
            OptSolution: solution
        """
        cloud_node = self.system.cloud_node
        for app in self.system.apps:
            if not solution.app_placement[app.id][cloud_node.id]:
                solution.app_placement[app.id][cloud_node.id] = True
                self._alloc_resources(app, cloud_node, solution, load=0.0, increment=False)
        return MOGAOperator._decode_part_3(self, individual, solution, selected_nodes)
