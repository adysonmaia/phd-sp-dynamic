from sp.core.heuristic.nsgaii import NSGAII
from sp.system_controller.optimizer.moga import MOGAOptimizer, MOGAOperator
from sp.system_controller.model import OptSolution
from sp.system_controller.util import calc_load_before_distribution, make_solution_feasible


class StaticOptimizer(MOGAOptimizer):
    """Static Optimizer

    """

    def __init__(self):
        """Initialization
        """
        MOGAOptimizer.__init__(self)
        self._init_solution = None
        self._init_encoded_solution = None

    def init_params(self):
        """Initialize parameters for a simulation
        """
        MOGAOptimizer.init_params(self)
        self._init_solution = None
        self._init_encoded_solution = None

    def solve(self, system, environment_input):
        """Solve the service placement problem

        Args:
            system (sp.core.model.system.System): current system's state
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        Returns:
            sp.system_controller.model.opt_solution.OptSolution: problem solution
        """
        solution = None
        ga_operator = _StaticGAOperator(objective=self.objective,
                                        system=system,
                                        environment_input=environment_input,
                                        use_heuristic=self.use_heuristic,
                                        extra_first_population=self._last_population,
                                        init_solution=self._init_solution)
        if self._init_solution is None:
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
            self._init_encoded_solution = population[0]
            self._init_solution = ga_operator.decode(self._init_encoded_solution)
            solution = self._init_solution
        else:
            solution = ga_operator.decode(self._init_encoded_solution)

        return solution


class _StaticGAOperator(MOGAOperator):
    """Static GA Operator

    Attributes:
        init_solution (OptSolution): initial solution, i.e., solution of the first time slot
    """

    def __init__(self, init_solution=None, **kwargs):
        MOGAOperator.__init__(**kwargs)
        self.init_solution = init_solution

    def decode(self, individual):
        """Decode the individual's chromosome and obtain a valid solution for the optimization problem

        Args:
            individual (GAIndividual): individual
        Returns:
            OptSolution: a valid solution
        """
        if self.init_solution is None:
            return MOGAOperator.decode(self, individual)
        else:
            return self._decode_static(individual)

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
            if solution.app_placement[app.id][cloud_node.id]:
                continue

            if cloud_node not in selected_nodes[app.id]:
                selected_nodes[app.id].append(cloud_node)

            if self._alloc_resources(app, cloud_node, solution, load=0.0, increment=False):
                solution.app_placement[app.id][cloud_node.id] = True

        return MOGAOperator._decode_part_3(self, individual, solution, selected_nodes)

    def _decode_static(self, individual):
        """Decode the individual's chromosome and obtain the static solution for the optimization problem

        Args:
            individual (GAIndividual): individual
        Returns:
            OptSolution: a valid solution
        """
        nb_apps = len(self.system.apps)
        nb_nodes = len(self.system.nodes)
        cloud_node = self.system.cloud_node
        solution = OptSolution.create_empty(self.system)

        # Set the same nodes as placement locations
        for app in self.system.apps:
            for node in self.system.nodes:
                if not self.init_solution.app_placement[app.id][node.id]:
                    continue
                if self._alloc_resources(app, node, solution, load=0.0, increment=False):
                    solution.app_placement[app.id][node.id] = True

        # It tries to use the same load distribution
        start = nb_apps * (nb_nodes + 1)
        end = self.nb_genes
        priority = individual[start:end]
        requests_index = list(range(len(self.requests)))
        requests_index.sort(key=lambda i: priority[i], reverse=True)
        for req_index in requests_index:
            app_id, src_node_id = self.requests[req_index]
            app = self.system.get_app(app_id)
            src_node = self.system.get_node(src_node_id)
            total_load = calc_load_before_distribution(app.id, src_node.id, self.system, self.environment_input)

            for dst_node in self.system.nodes:
                if not solution.app_placement[app.id][dst_node.id]:
                    continue

                ld = self.init_solution.load_distribution[app.id][src_node.id][dst_node.id]
                load = total_load * ld
                if self._alloc_resources(app, dst_node, solution, load):
                    solution.load_distribution[app.id][src_node.id][dst_node.id] += ld
                else:
                    self._alloc_resources(app, cloud_node, solution, load)
                    solution.load_distribution[app.id][src_node.id][cloud_node.id] += ld
                    solution.app_placement[app.id][cloud_node.id] = True

        return make_solution_feasible(self.system, solution, self.environment_input)
