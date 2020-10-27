from sp.core.model import Resource, Application
from sp.core.heuristic.brkga import GAOperator, GAIndividual
from sp.hierarchical_controller.global_ctrl.model import GlobalSystem, GlobalControlInput, GlobalEnvironmentInput
from sp.hierarchical_controller.global_ctrl.model import GlobalNode
from sp.hierarchical_controller.global_ctrl.util.calc import calc_load_before_distribution, calc_network_delay
from sp.hierarchical_controller.global_ctrl.util.calc import calc_processing_delay, calc_initialization_delay
from .cached_delays import GlobalCachedDelays
from collections import defaultdict
import math
import copy


DEFAULT_LOAD_CHUNK_DISTRIBUTION = 0.25


class GlobalMOGAOperator(GAOperator):
    """Genetic Operator for Global MOGA optimizer

    Attributes:
        objective (Union[list(function), function]): objective function(s) to be optimized
        system (GlobalSystem): system's state
        environment_input (GlobalControlInput): environment input
        use_heuristic (bool): use heuristic algorithms to generate the first population
        extra_first_population (list(GAIndividual)): list of individuals to be added in the first population
        load_chunk_distribution (float): load chunk distribution (value between 0 and 1).
            Loads are distributed in chunks where its size is defined by this attribute
    """

    def __init__(self, objective, system, environment_input,
                 use_heuristic=True,
                 extra_first_population=None,
                 load_chunk_distribution=None):
        """Initialization
        """
        GAOperator.__init__(self)
        self.system = system
        self.environment_input = environment_input
        self.objective = objective if isinstance(objective, list) else [objective]
        self.use_heuristic = use_heuristic
        self.extra_first_population = extra_first_population
        self.load_chunk_distribution = load_chunk_distribution
        if self.load_chunk_distribution is None:
            self.load_chunk_distribution = DEFAULT_LOAD_CHUNK_DISTRIBUTION

        nb_apps = len(self.system.apps)
        nb_nodes = len(self.system.nodes)
        self._nb_genes = 2 * nb_apps + 3 * nb_apps * nb_nodes
        self._requests = [(app.id, node.id) for app in self.system.apps for node in self.system.nodes]

    @property
    def requests(self):
        """Get source of requests for all applications

        Returns:
            requests (list): list of tuples (application's id, node's id)
        """
        return self._requests

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

    def first_population(self):
        """Generate some specific individuals for the first population based on heuristic algorithms

        Returns:
            individuals (list(GAIndividual)): list of individuals
        """
        from . import indiv_gen

        population = []
        if self.extra_first_population is not None:
            population += [indiv.clear_copy() for indiv in self.extra_first_population]

        if self.use_heuristic:
            heuristic_population = [
                indiv_gen.create_individual_cloud(self),
                indiv_gen.create_individual_net_delay(self),
                indiv_gen.create_individual_deadline(self),
                indiv_gen.create_individual_load(self),
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
        return False

    def evaluate(self, individual):
        """Evaluate an individual and obtain its fitness

        Args:
            individual (GAIndividual): individual
        Returns:
            object: fitness value
        """
        solution = self.decode(individual)
        fitness = [f(self.system, solution, self.environment_input) for f in self.objective]
        return fitness

    def decode(self, individual, debug=False):
        """Decode the individual's chromosome and obtain a valid solution for the global optimization problem

        Args:
            individual (GAIndividual): individual
        Returns:
            GlobalControlInput: a valid solution
        """
        self._debug = debug

        nb_apps = len(self.system.apps)
        nb_nodes = len(self.system.nodes)

        individual_parts = []
        parts_size = [nb_apps, nb_apps, nb_apps * nb_nodes, nb_apps * nb_nodes, nb_apps * nb_nodes]
        last_index = 0
        for part_index in range(len(parts_size)):
            part_size = parts_size[part_index]
            part = individual[last_index:last_index+part_size]
            individual_parts.append(part)
            last_index += part_size

        solution, selected_nodes, selected_nb_instances = self._decode_stage_1(individual_parts)
        solution = self._decode_stage_2(individual_parts, solution, selected_nodes, selected_nb_instances)
        solution = self._decode_stage_3(individual_parts, solution, selected_nodes, selected_nb_instances)

        return solution

    def _decode_stage_1(self, individual_parts):
        """Decode Stage I

        Args:
            individual_parts (list): individual splitted into parts
        Returns:
            (GlobalControlInput, dict, dict): solution, selected nodes per application,
            selected number of instances per application and node
        """
        all_apps = self.system.apps
        all_nodes = self.system.nodes
        nb_apps = len(all_apps)
        nb_nodes = len(all_nodes)
        nb_real_nodes = len(self.system.real_nodes)
        cloud_node = self.system.cloud_node
        cloud_index = self.system.nodes.index(cloud_node)

        solution = GlobalControlInput.create_empty(self.system)

        selected_nodes = {}
        selected_nb_instances = defaultdict(lambda: defaultdict(lambda: 0))
        for (a_index, app) in enumerate(all_apps):
            max_nb_instances = int(min(nb_real_nodes,
                                       math.ceil(individual_parts[0][a_index] * (app.max_instances - 1))))
            max_nb_nodes = int(min(max_nb_instances, math.ceil(individual_parts[1][a_index] * (nb_nodes - 1))))

            start = a_index * nb_nodes
            end = start + nb_nodes
            priority = individual_parts[2][start:end]
            priority[cloud_index] = -1
            nodes_index = list(range(nb_nodes))
            nodes_index.sort(key=lambda i: priority[i], reverse=True)
            nodes_index = nodes_index[:max_nb_nodes]

            app_nodes = list(map(lambda i: all_nodes[i], nodes_index))
            app_nodes.append(cloud_node)
            selected_nodes[app.id] = app_nodes

            percentages = individual_parts[3][start:end]
            normalize = float(sum(map(lambda i: percentages[i], nodes_index)))
            nb_selected_real_nodes = float(sum(map(lambda n: len(n.nodes), app_nodes)))

            if max_nb_instances >= nb_selected_real_nodes:
                for node_index in nodes_index:
                    node = all_nodes[node_index]
                    nb_instances = len(node.nodes)
                    selected_nb_instances[app.id][node.id] = nb_instances
            else:
                for node_index in nodes_index:
                    node = all_nodes[node_index]
                    selected_nb_instances[app.id][node.id] = 1

                    node_percentage = percentages[node_index]
                    normal_value = 0.0
                    if normalize > 0:
                        normal_value = node_percentage / normalize
                    else:
                        normal_value = 1.0 / max_nb_nodes
                    percentages[node_index] = normal_value

                remaining_instances = max_nb_instances - max_nb_nodes
                index = 0
                while remaining_instances > 0:
                    node_index = nodes_index[index]
                    node = all_nodes[node_index]
                    node_percentage = percentages[node_index]
                    nb_instances = int(max(1, math.floor(remaining_instances * node_percentage)))
                    if selected_nb_instances[app.id][node.id] + nb_instances <= len(node.nodes):
                        selected_nb_instances[app.id][node.id] += nb_instances
                        remaining_instances -= nb_instances

                    index = (index + 1) % len(nodes_index)

            # if self._debug:
            #     total = 0
            #     for node_index in nodes_index:
            #         node = all_nodes[node_index]
            #         nb_instances = selected_nb_instances[app.id][node.id]
            #         total += nb_instances
            #         print(app.id, node.id, max_nb_instances, len(node.nodes), nb_instances)
            #     print(app.id, max_nb_instances, total)

            selected_nb_instances[app.id][cloud_node.id] = 1

        return solution, selected_nodes, selected_nb_instances

    def _decode_stage_2(self, individual_parts, solution, selected_nodes, selected_nb_instances):
        """Decode Stage II

        Args:
            individual_parts (list): individual's parts
            solution (GlobalControlInput): solution
            selected_nodes (dict): selected nodes per application
            selected_nb_instances (dict): selected number of instances per application and node

        Returns:
            GlobalControlInput: solution
        """
        cloud_node = self.system.cloud_node
        cached_delays = GlobalCachedDelays()

        priority = individual_parts[4]
        requests_index = list(range(len(self.requests)))
        requests_index.sort(key=lambda i: priority[i], reverse=True)
        for req_index in requests_index:
            app_id, src_node_id = self.requests[req_index]
            app = self.system.get_app(app_id)
            src_node = self.system.get_node(src_node_id)

            total_load = calc_load_before_distribution(app.id, src_node.id, self.system, self.environment_input)
            remaining_load = total_load
            chunk = total_load * self.load_chunk_distribution
            max_nb_chunks = math.ceil(1.0 / float(self.load_chunk_distribution))
            chunk_count = 0

            if total_load <= 0.0:
                dst_node = cloud_node
                chunk = 0.0
                nb_instances = selected_nb_instances[app.id][dst_node.id]
                solution.load_distribution[app.id][src_node.id][dst_node.id] = 1.0
                self._alloc_resources(app, dst_node, solution, chunk, nb_instances, increment=True)
            else:
                app_nodes = list(selected_nodes[app.id])
                app_nodes.sort(key=lambda n: self._calc_response_time(app, src_node, n, solution,
                                                                      selected_nb_instances[app.id][n.id],
                                                                      cached_delays))
                while remaining_load > 0.0 and chunk_count < max_nb_chunks:
                    for dst_node in app_nodes:
                        nb_instances = selected_nb_instances[app.id][dst_node.id]
                        if nb_instances <= 0:
                            continue

                        if self._alloc_resources(app, dst_node, solution, chunk, nb_instances, increment=True):
                            chunk_ld = chunk / total_load if total_load > 0.0 else 1.0
                            solution.load_distribution[app.id][src_node.id][dst_node.id] += chunk_ld

                            remaining_load -= chunk
                            chunk = min(remaining_load, chunk)
                            chunk_count += 1
                            cached_delays.invalidate(app.id, src_node.id, dst_node.id)
                            break

                        # nb_instances_options = []
                        # if solution.app_placement[app.id][dst_node.id] > 0:
                        #     nb_instances_options = [solution.app_placement[app.id][dst_node.id]]
                        # elif selected_nb_instances[app.id][dst_node.id] > 0:
                        #     # nb_instances_options = list(
                        #     #     reversed(range(1, selected_nb_instances[app.id][dst_node.id] + 1)))
                        #     nb_instances_options = [selected_nb_instances[app.id][dst_node.id]]
                        #
                        # if len(nb_instances_options) <= 0:
                        #     continue
                        #
                        # placed = False
                        # index = 0
                        # while not placed and index < len(nb_instances_options):
                        #     nb_instances = nb_instances_options[index]
                        #
                        #     if self._alloc_resources(app, dst_node, solution, chunk, nb_instances, increment=True):
                        #         chunk_ld = chunk / total_load if total_load > 0.0 else 1.0
                        #         solution.load_distribution[app.id][src_node.id][dst_node.id] += chunk_ld
                        #
                        #         remaining_load -= chunk
                        #         chunk = min(remaining_load, chunk)
                        #         chunk_count += 1
                        #         cached_delays.invalidate(app.id, src_node.id, dst_node.id)
                        #         placed = True
                        #
                        #     index += 1
                        #
                        # if placed:
                        #     break

        return solution

    def _decode_stage_3(self, individual_parts, solution, selected_nodes, selected_nb_instances):
        """Decode Stage III

        Args:
            individual_parts (list): individual's parts
            solution (GlobalControlInput): solution
            selected_nodes (dict): selected nodes per application
            selected_nb_instances (dict): selected number of instances per application and node

        Returns:
            GlobalControlInput: solution
        """
        cloud_node = self.system.cloud_node
        for app in self.system.apps:
            nb_instances = solution.app_placement[app.id][cloud_node.id]
            nb_instances = int(max(1, nb_instances))
            solution.app_placement[app.id][cloud_node.id] = nb_instances

            app_nodes = list(selected_nodes[app.id])
            for dst_node in app_nodes:
                if solution.app_placement[app.id][dst_node.id] > 0:
                    continue

                nb_instances_options = []
                if selected_nb_instances[app.id][dst_node.id] > 0:
                    nb_instances_options = list(
                        reversed(range(1, selected_nb_instances[app.id][dst_node.id] + 1)))
                    for nb_instances in nb_instances_options:
                        chunk = 0.0
                        if self._alloc_resources(app, dst_node, solution, chunk, nb_instances, increment=False):
                            break

        return solution

    def _calc_response_time(self, app, src_node, dst_node, solution, nb_instances, cached_delays):
        """Calculate response time of requests from src_node to dst_node

        Args:
            app (Application): requested application
            src_node (GlobalNode): source node
            dst_node (GlobalNode): destination node
            solution (GlobalControlInput): solution
            nb_instances (int): number of application instances that should be placed in the global node
            cached_delays (CachedDelays): cached delays
        Returns:
            float: response time
        """
        if cached_delays.is_valid(app.id, src_node.id, dst_node.id):
            return cached_delays.get_rt(app.id, src_node.id, dst_node.id)

        prev_cpu_alloc = solution.allocated_resource[app.id][dst_node.id][Resource.CPU]
        prev_load = solution.received_load[app.id][dst_node.id]
        prev_place = solution.app_placement[app.id][dst_node.id]

        if prev_place <= 0:
            load = 0.0
            demand = app.demand[Resource.CPU](load)
            solution.allocated_resource[app.id][dst_node.id][Resource.CPU] = demand
            solution.received_load[app.id][dst_node.id] = load
            solution.app_placement[app.id][dst_node.id] = int(max(1, nb_instances))

        net_delay = None
        if cached_delays.is_net_delay_valid(app.id, src_node.id, dst_node.id):
            net_delay = cached_delays.get_net_delay(app.id, src_node.id, dst_node.id)
        else:
            net_delay = calc_network_delay(app.id, src_node.id, dst_node.id,
                                           self.system, solution, self.environment_input)
            cached_delays.set_net_delay(app.id, src_node.id, dst_node.id, net_delay)

        proc_delay = None
        if cached_delays.is_proc_delay_valid(app.id, dst_node.id):
            proc_delay = cached_delays.get_proc_delay(app.id, dst_node.id)
        else:
            proc_delay = calc_processing_delay(app.id, dst_node.id, self.system, solution, self.environment_input)
            cached_delays.set_proc_delay(app.id, dst_node.id, proc_delay)

        init_delay = None
        if cached_delays.is_init_delay_valid(app.id, dst_node.id):
            init_delay = cached_delays.get_init_delay(app.id, dst_node.id)
        else:
            init_delay = calc_initialization_delay(app.id, dst_node.id, self.system, solution, self.environment_input)
            cached_delays.set_init_delay(app.id, dst_node.id, init_delay)

        rt = net_delay + proc_delay + init_delay

        solution.allocated_resource[app.id][dst_node.id][Resource.CPU] = prev_cpu_alloc
        solution.received_load[app.id][dst_node.id] = prev_load
        solution.app_placement[app.id][dst_node.id] = prev_place

        return rt

    def _alloc_resources(self, app, node, solution, load, nb_instances=None, increment=True):
        """Allocate resources for an application in a node based on current load distribution and application placement

        Args:
            app (Application): application
            node (GlobalNode): node
            solution (GlobalControlInput): solution
            load (float): received load
            nb_instances (int): number of application instances
            increment (bool): whether the passed load should be added to the current load in the solution
        Returns:
            bool: it was possible to allocate resources or not
        """
        prev_load = solution.received_load[app.id][node.id]
        prev_alloc_res = copy.copy(solution.allocated_resource[app.id][node.id])
        prev_app_place = solution.app_placement[app.id][node.id]

        if nb_instances is None:
            nb_instances = prev_app_place

        if nb_instances > 0:
            load = load / float(nb_instances)
        else:
            load = 0.0

        if increment:
            solution.received_load[app.id][node.id] += load
        else:
            solution.received_load[app.id][node.id] = load

        load_per_instance = solution.received_load[app.id][node.id]
        for resource in self.system.resources:
            demand = app.demand[resource.name](load_per_instance)
            solution.allocated_resource[app.id][node.id][resource.name] = demand

        solution.app_placement[app.id][node.id] = nb_instances
        if not self._check_capacity_constraints(node, solution):
            solution.received_load[app.id][node.id] = prev_load
            solution.allocated_resource[app.id][node.id] = prev_alloc_res
            solution.app_placement[app.id][node.id] = prev_app_place
            return False
        else:
            return True

    def _check_capacity_constraints(self, node, solution):
        """Check if a solution respects capacity constraints in a specific global node

        Args:
            node (GlobalNode): node
            solution (GlobalControlInput): solution
        Returns:
            bool: constraint is satisfied or not
        """
        nb_real_nodes = len(node.nodes)
        alloc_res = solution.allocated_resource
        nb_instances = solution.app_placement
        for resource in self.system.resources:
            capacity = node.capacity[resource.name]
            total_capacity = nb_real_nodes * capacity
            total_demand = sum(map(lambda a: (alloc_res[a.id][node.id][resource.name] *
                                              nb_instances[a.id][node.id]),
                                   self.system.apps))
            if total_demand > total_capacity:
                return False

            for app in self.system.apps:
                app_instances = nb_instances[app.id][node.id]
                app_demand = alloc_res[app.id][node.id][resource.name]
                if app_instances > 0 and app_demand > capacity:
                    return False

        return True

