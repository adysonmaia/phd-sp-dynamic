from sp.core.model import Resource
from sp.core.heuristic.brkga import Chromosome
from sp.system_controller.model import OptSolution
from sp.system_controller.utils.opt import make_solution_feasible, calc_response_time
from . import individual_generator as indiv_gen
import math
import numpy

INF = float("inf")
POOL_SIZE = 4
DEFAULT_STALL_WINDOW = 30
DEFAULT_STALL_THRESHOLD = 0.0
DEFAULT_LOAD_CHUNK_PERCENT = 0.1


class SOChromosome(Chromosome):
    def __init__(self, system, objective, use_heuristic=True):
        Chromosome.__init__(self)
        self.system = system
        self.objective = objective
        self.use_heuristic = use_heuristic

        nb_apps = len(self.system.apps)
        nb_nodes = len(self.system.nodes)
        self.nb_genes = nb_apps * (2 * nb_nodes + 1)
        self.requests = [(app.id, node.id) for app in self.system.apps for node in self.system.nodes]

        self.load_chunk_percent = DEFAULT_LOAD_CHUNK_PERCENT

        self.stall_window = DEFAULT_STALL_WINDOW
        self.stall_threshold = DEFAULT_STALL_THRESHOLD
        self._best_values = []

    def init_params(self):
        Chromosome.init_params(self)
        self._best_values = []

    def gen_init_population(self):
        if not self.use_heuristic:
            return []

        indiv_list = [
            indiv_gen.create_individual_cloud(self),
            indiv_gen.create_individual_net_delay(self),
            indiv_gen.create_individual_cluster_metoids(self),
            indiv_gen.create_individual_deadline(self)
        ]
        merged_indiv = []
        for indiv_1 in indiv_list:
            indiv = indiv_gen.invert_individual(self, indiv_1)
            merged_indiv.append(indiv)

            for indiv_2 in indiv_list:
                if indiv_1 == indiv_2:
                    continue
                indiv = indiv_gen.merge_population(self, [indiv_1, indiv_2])
                merged_indiv.append(indiv)
        indiv_list += merged_indiv

        return indiv_list

    def stopping_criteria(self, population):
        best_indiv = population[0]
        best_value = best_indiv[self.nb_genes]

        variance = self.stall_threshold + 1
        self._best_values.append(best_value)
        if len(self._best_values) > self.stall_window:
            max_value = float(max(self._best_values))
            values = self._best_values[-1 * self.stall_window:]
            values = list(map(lambda i: i / max_value, values))
            variance = numpy.var(values)

        return best_value == 0.0 or variance <= self.stall_threshold

    def fitness(self, individual):
        solution = self.decode(individual)
        return self.objective(self.system, solution)

    def decode(self, individual):
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
            nodes_index.sort(key=lambda v: priority[v], reverse=True)
            percentage = individual[a_index]
            nb_instances = int(math.ceil(percentage * app.max_instances))
            max_nodes = min(nb_nodes, nb_instances)
            nodes_index = nodes_index[:max_nodes]

            selected_nodes[app.id] = list(map(lambda n_index: self.system.nodes[n_index], nodes_index))

        start = nb_apps * (nb_nodes + 1)
        end = start + self.nb_genes
        priority = individual[start:end]

        requests_index = list(range(len(self.requests)))
        requests_index.sort(key=lambda i: priority[i], reverse=True)
        for req_index in requests_index:
            app_id, src_node_id = self.requests[req_index]
            app = self.system.get_app(app_id)
            src_node = self.system.get_node(src_node_id)

            nodes = selected_nodes[app.id]
            nodes.sort(key=lambda n: calc_response_time(app, src_node, n, self.system, solution))
            nodes.append(cloud_node)

            total_load = float(self.system.get_request_load(app.id, src_node.id))
            remaining_load = total_load
            chunk = total_load * self.load_chunk_percent

            while remaining_load > 0.0:
                for dst_node in nodes:
                    solution.received_load[app.id][dst_node.id] += chunk
                    self._update_alloc_resources(app, dst_node, solution)

                    if self._check_capacity_constraint(dst_node, solution):
                        solution.app_placement[app.id][dst_node.id] = True
                        solution.load_distribution[app.id][src_node.id][dst_node.id] += chunk / total_load

                        remaining_load -= chunk
                        chunk = min(remaining_load, chunk)
                        break
                    else:
                        solution.received_load[app.id][dst_node.id] -= chunk
                        self._update_alloc_resources(app, dst_node, solution)

        return make_solution_feasible(solution)

    def _update_alloc_resources(self, app, node, solution):
        for resource in self.system.resources:
            load = solution.received_load[node.id][app.id]
            demand = app.demand[resource.name](load)
            solution.allocated_resource[app.id][node.id][resource.name] = demand
        return solution

    def _check_capacity_constraint(self, node, solution):
        alloc_res = solution.allocated_resource
        for resource in self.system.resources:
            capacity = node.capacity[resource.name]
            demand = sum(map(lambda a: alloc_res[a.id][node.id][resource.name], self.system.apps))
            if demand > capacity:
                return False
        return True

