from sp.core.model import Resource, Application, Node
from sp.core.heuristic.brkga import GAOperator, GAIndividual
from sp.system_controller.optimizer.soga.cached_delays import CachedDelays
from sp.hierarchical_controller.global_ctrl.model import GlobalNode
from sp.hierarchical_controller.cluster_ctrl.model import ClusterSystem, ClusterEnvironmentInput, ClusterControlInput
from sp.hierarchical_controller.cluster_ctrl.model import ClusterControlLimit
from sp.hierarchical_controller.cluster_ctrl.util.calc import calc_load_before_distribution, calc_initialization_delay
from sp.hierarchical_controller.cluster_ctrl.util.calc import calc_network_delay, calc_processing_delay
from collections import defaultdict
import math
import copy


DEFAULT_LOAD_CHUNK_DISTRIBUTION = 0.25


class ClusterMOGAOperator(GAOperator):
    """Generic Operator for Cluster MOGA optimizer

    Attributes:
        objective (Union[list(function), function]): objective function(s) to be optimized
        system (ClusterSystem): system's state
        environment_input (ClusterEnvironmentInput): environment input
        control_limit (ClusterControlLimit): global control input
        use_heuristic (bool): use heuristic algorithms to generate the first population
        extra_first_population (list(GAIndividual)): list of individuals to be added in the first population
        load_chunk_distribution (float): load chunk distribution (value between 0 and 1).
            Loads are distributed in chunks where its size is defined by this attribute
    """

    def __init__(self, objective, system, environment_input,
                 control_limit=None,
                 use_heuristic=True,
                 extra_first_population=None,
                 load_chunk_distribution=None):
        """Initialization
        """
        GAOperator.__init__(self)
        self.system = system
        self.environment_input = environment_input
        self.control_limit = control_limit
        self.objective = objective if isinstance(objective, list) else [objective]
        self.use_heuristic = use_heuristic
        self.extra_first_population = extra_first_population
        self.load_chunk_distribution = load_chunk_distribution
        if self.load_chunk_distribution is None:
            self.load_chunk_distribution = DEFAULT_LOAD_CHUNK_DISTRIBUTION

        nb_apps = len(self.system.apps)
        nb_internal_nodes = len(self.system.internal_nodes)
        nb_all_nodes = len(self.system.nodes)

        self._nb_genes = nb_apps * (1 + nb_internal_nodes + nb_all_nodes)
        self._requests = [(app.id, node.id) for app in self.system.apps for node in self.system.nodes]
        self._max_dispatching_load = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

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
        self._init_limits()

    def _init_limits(self):
        """Initialize constraint limits
        """
        for app in self.system.apps:
            for src_node in self.system.internal_nodes:
                for dst_node in self.system.internal_nodes:
                    self._max_dispatching_load[app.id][src_node.id][dst_node.id] = math.inf
                for dst_node in self.system.external_nodes:
                    max_load = math.inf
                    if self.control_limit is not None:
                        max_load = self.control_limit.get_max_dispatch_load(app.id, dst_node.id)
                    self._max_dispatching_load[app.id][src_node.id][dst_node.id] = max_load
            for src_node in self.system.external_nodes:
                for dst_node in self.system.internal_nodes:
                    self._max_dispatching_load[app.id][src_node.id][dst_node.id] = math.inf
                for dst_node in self.system.external_nodes:
                    max_load = 0.0
                    if dst_node.is_cloud():
                        max_load = math.inf
                    self._max_dispatching_load[app.id][src_node.id][dst_node.id] = max_load

    def first_population(self):
        """Generate some specific individuals for the first population based on heuristic algorithms

        Returns:
            individuals (list(GAIndividual)): list of individuals
        """
        from . import indiv_gen

        population = []
        if self.extra_first_population is not None:
            population += [indiv.clear_copy() for indiv in self.extra_first_population]

        # TODO: create global heuristics
        if self.use_heuristic:
            heuristic_population = [
                indiv_gen.create_individual_cloud(self),
                indiv_gen.create_individual_net_delay(self),
                # indiv_gen.create_individual_cluster_metoids(self),
                indiv_gen.create_individual_deadline(self),
                indiv_gen.create_individual_load(self),
                # indiv_gen.create_individual_current(self)
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
        return [f(self.system, solution, self.environment_input) for f in self.objective]

    def decode(self, individual):
        """Decode the individual's chromosome and obtain a valid solution for the global optimization problem

        Args:
            individual (GAIndividual): individual
        Returns:
            ClusterControlInput: a valid solution
        """
        nb_apps = len(self.system.apps)
        nb_internal_nodes = len(self.system.internal_nodes)
        nb_all_nodes = len(self.system.nodes)

        individual_parts = []
        parts_size = [nb_apps, nb_apps * nb_internal_nodes, nb_apps * nb_all_nodes]
        last_index = 0
        for part_index in range(len(parts_size)):
            part_size = parts_size[part_index]
            part = individual[last_index:last_index + part_size]
            individual_parts.append(part)
            last_index += part_size

        solution = self._decode_stage_1(individual_parts)
        solution, selected_nodes = self._decode_stage_2(individual_parts, solution)
        solution = self._decode_stage_3(individual_parts, solution, selected_nodes)
        solution = self._decode_stage_4(individual_parts, solution, selected_nodes)

        return solution

    def _decode_stage_1(self, individual_parts):
        """Decode Stage I

        Args:
            individual_parts (list(list)): individual's parts

        Returns:
            ClusterControlInput: solution
        """
        self._init_limits()
        solution = ClusterControlInput.create_empty(self.system)
        for app in self.system.apps:
            for ext_node in self.system.external_nodes:
                nb_instances = self.environment_input.get_nb_instances(app.id, ext_node.id)
                if ext_node.is_cloud():
                    nb_instances = int(max(1, nb_instances))
                if nb_instances > 0:
                    load = self.environment_input.get_additional_received_load(app.id, ext_node.id)
                    if self._alloc_resources(app, ext_node, solution, load, increment=False):
                        solution.app_placement[app.id][ext_node.id] = True
        return solution

    def _decode_stage_2(self, individual_parts, solution):
        """Decode Stage II

        Args:
            individual_parts (list(list)): individual's parts
            solution (ClusterControlInput): solution

        Returns:
            (ClusterControlInput, dict): solution, selected nodes per application
        """
        nb_apps = len(self.system.apps)
        internal_nodes = self.system.internal_nodes
        nb_internal_nodes = len(internal_nodes)

        selected_nodes = {}
        for (a_index, app) in enumerate(self.system.apps):
            start = a_index * nb_internal_nodes
            end = start + nb_internal_nodes
            priority = individual_parts[1][start:end]

            max_nb_instances = app.max_instances
            min_nb_instances = 0
            if self.control_limit is not None:
                max_nb_instances = self.control_limit.get_max_app_placement(app.id)
                min_nb_instances = self.control_limit.get_min_app_placement(app.id)
            max_nb_instances = min(max_nb_instances, nb_internal_nodes)

            nodes_index = list(range(nb_internal_nodes))
            nodes_index.sort(key=lambda i: priority[i], reverse=True)
            percentage = individual_parts[0][a_index]
            nb_instances = int(min(nb_internal_nodes, max(min_nb_instances, math.ceil(percentage * max_nb_instances))))

            selected_nodes_index = nodes_index[:nb_instances]
            selected_nodes[app.id] = list(map(lambda n_index: internal_nodes[n_index], selected_nodes_index))

        return solution, selected_nodes

    def _decode_stage_3(self, individual_parts, solution, selected_nodes):
        """Decode Stage III.
        It distributes load among the selected nodes of stage I

        Args:
            individual_parts (list(list)): individual's parts
            solution (ClusterControlInput): solution
            selected_nodes (dict): selected nodes of part I
        Returns:
            ClusterControlInput: solution
        """
        nb_apps = len(self.system.apps)
        nb_all_nodes = len(self.system.nodes)

        priority = individual_parts[2]
        cached_delays = CachedDelays()

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

            if total_load > 0.0:
                nodes = list(selected_nodes[app.id])
                for ext_node in self.system.external_nodes:
                    max_load = self._max_dispatching_load[app.id][src_node.id][ext_node.id]
                    place = solution.app_placement[app.id][ext_node.id]
                    if max_load > 0 and place:
                        nodes.append(ext_node)

                nodes.sort(key=lambda n: self._calc_response_time(app, src_node, n, solution, cached_delays))
                while remaining_load > 0.0 and chunk_count < max_nb_chunks:
                    for dst_node in nodes:
                        if self._alloc_resources(app, dst_node, solution, chunk, increment=True):
                            solution.app_placement[app.id][dst_node.id] = True
                            chunk_ld = chunk / total_load if total_load > 0.0 else 1.0
                            solution.load_distribution[app.id][src_node.id][dst_node.id] += chunk_ld

                            remaining_load -= chunk
                            chunk = min(remaining_load, chunk)
                            chunk_count += 1
                            cached_delays.invalidate(app.id, src_node.id, dst_node.id)
                            break

        return solution

    def _decode_stage_4(self, individual_parts, solution, selected_nodes):
        """Decode Stage IV.
        It is a local search to make solution feasible

        Args:
            individual_parts (list(list)): individual's parts
            solution (OptSolution): solution
            selected_nodes (dict): selected nodes of part II
        Returns:
            OptSolution: solution
        """
        for app in self.system.apps:
            for dst_node in selected_nodes[app.id]:
                if solution.app_placement[app.id][dst_node.id]:
                    continue

                if self._alloc_resources(app, dst_node, solution, load=0.0, increment=False):
                    solution.app_placement[app.id][dst_node.id] = True

        # TODO: check feasibility
        return solution

    def _calc_response_time(self, app, src_node, dst_node, solution, cached_delays):
        """Calculate response time of requests from src_node to dst_node

        Args:
            app (Application): requested application
            src_node (Node): source node
            dst_node (Node): destination node
            solution (ClusterControlInput): solution
            cached_delays (CachedDelays): cached delays
        Returns:
            float: response time
        """
        if cached_delays.is_valid(app.id, src_node.id, dst_node.id):
            return cached_delays.get_rt(app.id, src_node.id, dst_node.id)

        prev_cpu_alloc = solution.allocated_resource[app.id][dst_node.id][Resource.CPU]
        prev_load = solution.received_load[app.id][dst_node.id]
        prev_place = solution.app_placement[app.id][dst_node.id]

        if not prev_place:
            load = 0.0
            demand = app.demand[Resource.CPU](load)
            solution.allocated_resource[app.id][dst_node.id][Resource.CPU] = demand
            solution.received_load[app.id][dst_node.id] = load
            solution.app_placement[app.id][dst_node.id] = True

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

    def _alloc_resources(self, app, node, solution, load, increment=True):
        """Allocate resources for an application in a node based on current load distribution and application placement

        Args:
            app (Application): application
            node (Node): node
            solution (ClusterControlInput): solution
            load (float): received load
            increment (bool): whether the passed load should be added to the current load in the solution
        Returns:
            bool: it was possible to allocate resources or not
        """
        prev_load = solution.received_load[app.id][node.id]
        prev_alloc_res = copy.copy(solution.allocated_resource[app.id][node.id])

        if isinstance(node, GlobalNode):
            nb_instance = self.environment_input.get_nb_instances(app.id, node.id)
            if nb_instance > 0:
                load = load / float(nb_instance)

        if increment:
            solution.received_load[app.id][node.id] += load
        else:
            solution.received_load[app.id][node.id] = load
        load = solution.received_load[app.id][node.id]
        for resource in self.system.resources:
            demand = app.demand[resource.name](load)
            solution.allocated_resource[app.id][node.id][resource.name] = demand

        if not self._check_constraints(node, solution):
            solution.received_load[app.id][node.id] = prev_load
            solution.allocated_resource[app.id][node.id] = prev_alloc_res
            return False
        else:
            return True

    def _check_constraints(self, node, solution):
        """Check if a solution respects constraints in a specific node

        Args:
            node (Node):
            solution (ClusterControlInput): solution
        Returns:
            bool: constraint is satisfied or not
        """
        if isinstance(node, GlobalNode):
            for app in self.system.apps:
                load = solution.received_load[app.id][node.id]
                init_load = self.environment_input.get_additional_received_load(app.id, node.id)
                max_load = math.inf
                if self.control_limit is not None:
                    max_load = self.control_limit.get_max_dispatch_load(app.id, node.id)
                return (load - init_load) <= max_load
        else:
            alloc_res = solution.allocated_resource
            for resource in self.system.resources:
                capacity = node.capacity[resource.name]
                demand = sum(map(lambda a: alloc_res[a.id][node.id][resource.name], self.system.apps))
                if demand > capacity:
                    return False
        return True

