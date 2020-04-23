from sp.core.model import Resource
from sp.core.heuristic.brkga import GAOperator, GAIndividual
from sp.system_controller.model import OptSolution
from sp.system_controller.util import make_solution_feasible
from sp.system_controller.util import calc_response_time, calc_load_before_distribution
from . import indiv_gen
import math
import numpy
import copy


DEFAULT_STALL_WINDOW = 30
DEFAULT_STALL_THRESHOLD = 0.0
DEFAULT_LOAD_CHUNK_PERCENT = 0.1


class SOGAOperator(GAOperator):
    """ Genetic Operator for SOGA optimizer
    """

    def __init__(self, objective, system, environment_input, use_heuristic=True, first_population=None):
        """Initialization
        Args:
            objective (function): objective function to be optimized
            system (sp.core.model.System): system's state
            environment_input (sp.core.mode.EnvironmentInput): environment input
            use_heuristic (bool): use heuristic algorithms to generate the first population
            first_population (list(GAIndividual)): list of individuals to be added in the first population
        """
        GAOperator.__init__(self)
        self.system = system
        self.environment_input = environment_input
        self.objective = objective
        self.use_heuristic = use_heuristic
        self.extended_first_population = first_population

        nb_apps = len(self.system.apps)
        nb_nodes = len(self.system.nodes)
        self._nb_genes = nb_apps * (2 * nb_nodes + 1)
        self.requests = [(app.id, node.id) for app in self.system.apps for node in self.system.nodes]

        self.load_chunk_percent = DEFAULT_LOAD_CHUNK_PERCENT

        self.stall_window = DEFAULT_STALL_WINDOW
        self.stall_threshold = DEFAULT_STALL_THRESHOLD
        self._best_values = []

    @property
    def nb_genes(self):
        """Number of genes of an individual's chromosome
        Returns:
            int: number of genes
        """
        return self._nb_genes

    def init_params(self):
        """Initialize parameters before starting the genetic algorithm
        """
        GAOperator.init_params(self)
        self._best_values = []

    def first_population(self):
        """Generate some specific individuals for the first population based on heuristic algorithms
        Returns:
            individuals (list(GAIndividual)): list of individuals
        """
        population = []
        if self.extended_first_population is not None:
            population += [indiv.clear_copy() for indiv in self.extended_first_population]

        if self.use_heuristic:
            heuristic_population = [
                indiv_gen.create_individual_cloud(self),
                indiv_gen.create_individual_net_delay(self),
                # indiv_gen.create_individual_cluster_metoids(self),
                indiv_gen.create_individual_deadline(self),
                indiv_gen.create_individual_load(self),
                indiv_gen.create_individual_current(self)
            ]
            merged_population = []
            for indiv_1 in heuristic_population:
                indiv = indiv_gen.invert_individual(self, indiv_1)
                merged_population.append(indiv)

                for indiv_2 in heuristic_population:
                    if indiv_1 != indiv_2:
                        indiv = indiv_gen.merge_population(self, [indiv_1, indiv_2])
                        merged_population.append(indiv)
            population += heuristic_population + merged_population

        return population

    def should_stop(self, population):
        """Verify whether genetic algorithm should stop or not
        Args:
           population (list(GAIndividual)): population of the current generation
        Returns:
           bool: True if genetic algorithm should stop, False otherwise
        """
        best_indiv = population[0]
        best_value = best_indiv.fitness

        variance = self.stall_threshold + 1
        self._best_values.append(best_value)
        if len(self._best_values) > self.stall_window:
            max_value = float(max(self._best_values))
            values = self._best_values[-1 * self.stall_window:]
            values = list(map(lambda i: i / max_value, values))
            variance = numpy.var(values)

        return best_value == 0.0 or variance <= self.stall_threshold

    def evaluate(self, individual):
        """Evaluate an individual and obtain its fitness
        Args:
            individual (GAIndividual): individual
        Returns:
            object: fitness value
        """
        solution = self.decode(individual)
        return self.objective(self.system, solution, self.environment_input)

    def decode(self, individual):
        """Decode the individual's chromosome and obtain a valid solution for the optimization problem
        Args:
            individual (GAIndividual): individual
        Returns:
            OptSolution: a valid solution
        """
        nb_apps = len(self.system.apps)
        nb_nodes = len(self.system.nodes)
        cloud_node = self.system.cloud_node

        solution = OptSolution.create_empty(self.system)

        selected_nodes = {}
        for (a_index, app) in enumerate(self.system.apps):
            start = nb_apps + a_index * nb_nodes
            end = start + nb_nodes
            priority = individual[start:end]

            nodes_index = list(range(nb_nodes))
            nodes_index.sort(key=lambda i: priority[i], reverse=True)
            percentage = individual[a_index]
            max_nb_instances = min(nb_nodes, app.max_instances)
            nb_instances = int(math.ceil(percentage * max_nb_instances))
            max_nb_nodes = min(nb_nodes, nb_instances)
            nodes_index = nodes_index[:max_nb_nodes]

            nodes = list(map(lambda n_index: self.system.nodes[n_index], nodes_index))
            selected_nodes[app.id] = nodes

        start = nb_apps * (nb_nodes + 1)
        end = self.nb_genes
        priority = individual[start:end]

        requests_index = list(range(len(self.requests)))
        requests_index.sort(key=lambda i: priority[i], reverse=True)
        for req_index in requests_index:
            app_id, src_node_id = self.requests[req_index]
            app = self.system.get_app(app_id)
            src_node = self.system.get_node(src_node_id)

            nodes = list(selected_nodes[app.id])
            nodes.append(cloud_node)
            nodes.sort(key=lambda n: self._calc_response_time(app, src_node, n, solution))

            place_nodes = []

            total_load = calc_load_before_distribution(app.id, src_node.id, self.system, self.environment_input)
            chunk = total_load * self.load_chunk_percent
            remaining_load = total_load

            while True:
                for dst_node in nodes:
                    if self._alloc_resources(app, dst_node, solution, chunk, increment=True):
                        solution.app_placement[app.id][dst_node.id] = True
                        chunk_ld = chunk / total_load if total_load > 0.0 else 1.0
                        solution.load_distribution[app.id][src_node.id][dst_node.id] += chunk_ld

                        remaining_load -= chunk
                        chunk = min(remaining_load, chunk)

                        if dst_node not in place_nodes:
                            place_nodes.append(dst_node)
                        break

                if remaining_load <= 0.0:
                    break

        for app in self.system.apps:
            for dst_node in selected_nodes[app.id]:
                if solution.app_placement[app.id][dst_node.id]:
                    continue

                if self._alloc_resources(app, dst_node, solution, load=0.0, increment=False):
                    solution.app_placement[app.id][dst_node.id] = True

        return make_solution_feasible(self.system, solution, self.environment_input)

    def _alloc_resources(self, app, node, solution, load, increment=True):
        prev_load = solution.received_load[app.id][node.id]
        prev_alloc_res = copy.copy(solution.allocated_resource[app.id][node.id])

        if increment:
            solution.received_load[app.id][node.id] += load
        else:
            solution.received_load[app.id][node.id] = load
        load = solution.received_load[app.id][node.id]
        for resource in self.system.resources:
            demand = app.demand[resource.name](load)
            solution.allocated_resource[app.id][node.id][resource.name] = demand

        if not self._check_capacity_constraint(node, solution):
            solution.received_load[app.id][node.id] = prev_load
            solution.allocated_resource[app.id][node.id] = prev_alloc_res
            return False
        else:
            return True

    def _check_capacity_constraint(self, node, solution):
        alloc_res = solution.allocated_resource
        for resource in self.system.resources:
            capacity = node.capacity[resource.name]
            demand = sum(map(lambda a: alloc_res[a.id][node.id][resource.name], self.system.apps))
            if demand > capacity:
                return False
        return True

    def _calc_response_time(self, app, src_node, dst_node, solution):
        prev_cpu_alloc = solution.allocated_resource[app.id][dst_node.id][Resource.CPU]
        prev_load = solution.received_load[app.id][dst_node.id]
        prev_place = solution.app_placement[app.id][dst_node.id]

        if not prev_place:
            load = 0.0
            demand = app.demand[Resource.CPU](load)
            solution.allocated_resource[app.id][dst_node.id][Resource.CPU] = demand
            solution.received_load[app.id][dst_node.id] = load
            solution.app_placement[app.id][dst_node.id] = True

        rt = calc_response_time(app.id, src_node.id, dst_node.id, self.system, solution, self.environment_input)

        solution.allocated_resource[app.id][dst_node.id][Resource.CPU] = prev_cpu_alloc
        solution.received_load[app.id][dst_node.id] = prev_load
        solution.app_placement[app.id][dst_node.id] = prev_place

        return rt

