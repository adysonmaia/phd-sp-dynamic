from sp.heuristic.brkga import Chromosome
from sp.model.allocation import Allocation
from sp.solver.utils import local_search
from . import individual_generator as indiv_gen
from collections import defaultdict
import math
import numpy

INF = float("inf")
POOL_SIZE = 4
DEFAULT_STALL_WINDOW = 30
DEFAULT_STALL_THRESHOLD = 0.0
LOAD_CHUNK_PERCENT = 0.1


class SOGAChromosome(Chromosome):
    def __init__(self, system, objective, use_heuristic=True):
        Chromosome.__init__(self)
        self.system = system
        self.objective = objective
        self.use_heuristic = use_heuristic

        nb_apps = len(self.system.apps)
        nb_nodes = len(self.system.nodes)
        self.nb_genes = nb_apps * (2 * nb_nodes + 1)
        self.requests = [(app.id, node.id) for app in self.system.apps for node in self.system.nodes]

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
        result = self.decode(individual)
        return self.objective(*result)

    def decode(self, individual):
        nb_apps = len(self.system.apps)
        nb_nodes = len(self.system.nodes)
        cloud_node = self.system.cloud_node

        alloc = Allocation.create_empty(self.system)
        alloc.received_load = defaultdict(lambda: defaultdict(float))

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
            nodes.sort(key=lambda n: self._node_priority(app, src_node, n, alloc))
            nodes.append(cloud_node)

            total_load = float(self.system.get_request_load(app.id, src_node.id))
            remaining_load = total_load
            chunk = total_load * LOAD_CHUNK_PERCENT

            while remaining_load > 0.0:
                for dst_node in nodes:
                    alloc[dst_node.id][app.id] += chunk
                    if self._check_capacity_constraint(dst_node, alloc):
                        alloc.set_app_placement(app.id, dst_node.id, True)
                        ld = alloc.get_load_distribution(app.id, src_node.id, dst_node.id)
                        ld += chunk / total_load
                        alloc.set_load_distribution(app.id, src_node.id, dst_node.id, ld)
                        remaining_load -= chunk
                        chunk = min(remaining_load, chunk)
                        break
                    else:
                        alloc[dst_node.id][app.id] -= chunk

        del alloc.received_load
        return local_search(alloc)

    def _check_capacity_constraint(self, node, alloc):
        # TODO: improve the performance of this method
        for resource in self.system.resources:
            capacity = node.capacity[resource.name]
            demand = 0.0
            for app in self.system.apps:
                demand += app.demand[resource.name](alloc.received_load[node.id][app.id])
            if demand > capacity:
                return False
        return True

    def _node_priority(self, app, src_node, dst_node, alloc):
        net_delay = self.system.get_net_delay(app.id, src_node.id, dst_node.id)

        arrival_rate = alloc.received_load[dst_node.id][app.id]
        service_rate = app.cpu_demand(arrival_rate) / float(app.work_size)
        proc_delay = INF
        if service_rate > arrival_rate:
            proc_delay = 1.0 / float(service_rate - arrival_rate)

        return net_delay + proc_delay

