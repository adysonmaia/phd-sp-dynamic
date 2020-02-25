from sp.heuristic.brkga import BRKGA, Chromosome
import math
import numpy

INF = float("inf")
POOL_SIZE = 4
DEFAULT_STALL_WINDOW = 30
DEFAULT_STALL_THRESHOLD = 0.0


class SOGAChromosome(Chromosome):
    def __init__(self, system, objective, use_heuristic=True):
        Chromosome.__init__(self)
        self.system = system
        self.objective = objective
        self.use_heuristic = use_heuristic

        nb_apps = len(self.system.apps)
        nb_nodes = len(self.system.nodes)

        self.requests = []
        for app in self.system.apps:
            for node in self.system.nodes:
                load = self.system.get_request_load(app.id, node.id)
                self.requests += [(app.id, node.id)] * math.ceil(load)

        self.nb_genes = nb_apps * (nb_nodes + 1) + len(self.requests)

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
            ga_heuristic.create_individual_cloud(self),
            ga_heuristic.create_individual_net_delay(self),
            ga_heuristic.create_individual_cluster_metoids(self),
            ga_heuristic.create_individual_deadline(self)
        ]
        merged_indiv = []
        for indiv_1 in indiv_list:
            indiv = ga_heuristic.invert_individual(self, indiv_1)
            merged_indiv.append(indiv)

            for indiv_2 in indiv_list:
                if indiv_1 == indiv_2:
                    continue
                indiv = ga_heuristic.merge_population(self, [indiv_1, indiv_2])
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
        nb_apps = len(self.apps)
        r_apps = range(nb_apps)
        nb_nodes = len(self.nodes)
        r_nodes = range(nb_nodes)
        nb_requests = len(self.requests)
        r_requests = range(nb_requests)
        cloud = self.get_cloud_index()

        place = {(a, h): 0
                 for h in r_nodes
                 for a in r_apps}
        load = {(a, b, h): 0
                for h in r_nodes
                for b in r_nodes
                for a in r_apps}
        app_load = {(a, h): 0
                    for h in r_nodes
                    for a in r_apps}

        selected_nodes = []
        for a in r_apps:
            app = self.apps[a]
            start = nb_apps + a * nb_nodes
            end = start + nb_nodes
            priority = individual[start:end]

            nodes = list(r_nodes)
            nodes.sort(key=lambda v: priority[v], reverse=True)
            percentage = individual[a]
            nb_instances = int(math.ceil(percentage * app.max_instances))
            max_nodes = min(nb_nodes, nb_instances)
            selected_nodes.append(nodes[:max_nodes])

        resource_used = {(h, r): 0 for h in r_nodes for r in self.resources}

        start = nb_apps * (nb_nodes + 1)
        end = start + nb_requests
        priority = individual[start:end]

        s_requests = sorted(r_requests, key=lambda v: priority[v], reverse=True)
        for req in s_requests:
            a, b = self.requests[req]
            nodes = list(selected_nodes[a])
            nodes.sort(key=lambda h: self._node_priority(individual,
                                                         a, b, h, app_load))
            nodes.append(cloud)
            for h in nodes:
                fit = True
                resources = {}
                for r in self.resources:
                    k1, k2 = self.apps[a].get_demand(r)
                    value = resource_used[h, r] + k1 + (1 - place[a, h]) * k2
                    capacity = self.nodes[h].get_capacity(r)
                    resources[r] = value
                    fit = fit and (value <= capacity)

                if fit:
                    load[a, b, h] += 1
                    app_load[a, h] += 1
                    place[a, h] = 1
                    for r in self.resources:
                        resource_used[h, r] = resources[r]
                    break

        return self.local_search(place, load)

    def _node_priority(self, indiv, a, b, h, app_load):
        app = self.apps[a]
        work_size = app.work_size
        cpu_k1, cpu_k2 = app.get_cpu_demand()

        proc_delay = 0.0
        net_delay = self.get_net_delay(a, b, h)

        # new request + current load
        node_load = 1 + app_load[a, h]
        proc_delay_divisor = float(node_load * (cpu_k1 - work_size) + cpu_k2)
        if proc_delay_divisor > 0.0:
            proc_delay = work_size / proc_delay_divisor
        else:
            proc_delay = INF

        return net_delay + proc_delay

