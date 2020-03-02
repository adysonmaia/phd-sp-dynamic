from sp.core.heuristic.kmedoids import KMedoids

INF = float("inf")


def create_individual_empty(chromosome):
    """Create a default individual
    """
    return [0.0] * chromosome.nb_genes


def create_individual_cloud(chromosome):
    """Create an individual that prioritizes the cloud node
    """
    return [0.0] * chromosome.nb_genes


def create_individual_net_delay(chromosome):
    """Create an individual that prioritizes nodes having shorter avg. net delays to other nodes
    and requests with strict deadlines
    """
    system = chromosome.system
    nb_apps = len(system.apps)
    nb_nodes = len(system.nodes)

    indiv = create_individual_empty(chromosome)
    for (a_index, app) in enumerate(system.apps):
        indiv[a_index] = 1.0

        nodes_delay = []
        max_delay = 1.0
        for (dst_index, dst_node) in enumerate(system.nodes):
            avg_delay = 0.0
            count = 0
            for (src_index, src_node) in enumerate(system.nodes):
                avg_delay += system.get_net_delay(app.id, src_node.id, dst_node.id)
                count += 1
            if count > 0:
                avg_delay = avg_delay / float(count)
            nodes_delay.append(avg_delay)
            if avg_delay > max_delay:
                max_delay = avg_delay

        for (dst_index, dst_node) in enumerate(system.nodes):
            key = nb_apps + a_index * nb_nodes + dst_index
            value = 1.0 - nodes_delay[dst_index] / float(max_delay)
            indiv[key] = value

    return indiv


def create_individual_cluster_metoids(chromosome, use_sc=False):
    """Create an individual based on k-medoids clustering.
    The idea is the users of an application are grouped and central nodes of each group are prioritized.
    It also prioritizes requests with strict deadlines
    """
    system = chromosome.system
    nb_apps = len(system.apps)
    nb_nodes = len(system.nodes)
    kmedoids = KMedoids()

    indiv = create_individual_empty(chromosome)
    for (a_index, app) in enumerate(system.apps):
        indiv[a_index] = 1.0

        distances = [[float(system.get_net_delay(app.id, src_node.id, dst_node.id))
                      for dst_node in system.nodes]
                     for src_node in system.nodes]

        features = [n_index for (n_index, node) in enumerate(system.nodes)
                    if system.get_generated_load(app.id, node.id) > 0]

        max_nb_clusters = int(min(len(features), app.max_instances))
        min_nb_clusters = 1 if use_sc else max_nb_clusters

        metoids = list(range(nb_nodes))
        max_score = -1
        if max_nb_clusters > 1:
            for k in range(min_nb_clusters, max_nb_clusters + 1):
                k_clusters = kmedoids.fit(k, features, distances)
                k_score = kmedoids.silhouette_score(k_clusters, distances)
                k_metoids = kmedoids.get_last_metoids()
                if k_score > max_score:
                    max_score = k_score
                    metoids = k_metoids

        m_distances = []
        max_dist = 1.0
        for (n_index, node) in enumerate(system.nodes):
            dist = min(map(lambda m: distances[n_index][m], metoids))
            m_distances.append(dist)
            if dist > max_dist:
                max_dist = dist

        for (n_index, node) in enumerate(system.nodes):
            key = nb_apps + a_index * nb_nodes + n_index
            value = 1.0 - m_distances[n_index] / float(max_dist)
            indiv[key] = value

    return indiv


def create_individual_cluster_metoids_sc(chromosome):
    """Create an individual based on k-medoids clustering with silhouette score.
    The idea is the users of an application are grouped and central nodes of each group are prioritized.
    It also prioritizes requests with strict deadlines
    """
    return create_individual_cluster_metoids(chromosome, use_sc=True)


def create_individual_load(chromosome):
    """Create an individual that prioritizes nodes with large load
    """
    system = chromosome.system
    nb_apps = len(system.apps)
    nb_nodes = len(system.nodes)

    indiv = create_individual_empty(chromosome)
    max_deadline = 1.0
    max_load = 0.0

    for (a_index, app) in enumerate(system.apps):
        indiv[a_index] = 1.0
        deadline = app.deadline
        if deadline > max_deadline:
            max_deadline = deadline

        max_app_load = 0.0
        for (n_index, node) in enumerate(system.nodes):
            key = nb_apps + a_index * nb_nodes + n_index
            load = system.get_generated_load(app.id, node.id)
            value = load
            indiv[key] = value
            if load > max_app_load:
                max_app_load = load
            if load > max_load:
                max_load = load
        if max_app_load > 0.0:
            for (n_index, node) in enumerate(system.nodes):
                key = nb_apps + a_index * nb_nodes + n_index
                value = indiv[key] / float(max_app_load)
                indiv[key] = value

    for (req_index, req) in enumerate(chromosome.requests):
        app_id, node_id = req
        key = nb_apps * (nb_nodes + 1) + req_index
        value = system.get_generated_load(app_id, node_id)
        if max_load > 0.0:
            value = value / float(max_load)
        indiv[key] = value

    return indiv


def create_individual_capacity(chromosome):
    """Create an individual that prioritizes nodes with high capacity of resources
    """
    system = chromosome.system
    nb_apps = len(system.apps)
    nb_nodes = len(system.nodes)
    nb_resources = len(system.resources)

    indiv = create_individual_empty(chromosome)

    max_capacity = {r.name: 1.0 for r in system.resources}
    for (n_index, node) in enumerate(system.nodes):
        for resource in system.resources:
            capacity = node.capacity[resource.name]
            if capacity > max_capacity[resource.name] and capacity != INF:
                max_capacity[resource.name] = float(capacity)

    node_priority = [0 for _ in system.nodes]
    for (n_index, node) in enumerate(system.nodes):
        value = 0.0
        for resource in system.resources:
            capacity = node.capacity[resource.name]
            if capacity == INF:
                value += 1.0
            else:
                value += capacity / max_capacity[resource.name]
        value = value / float(nb_resources)
        node_priority[n_index] = value

    for (a_index, app) in enumerate(system.apps):
        indiv[a_index] = 1.0
        for (n_index, node) in enumerate(system.nodes):
            key = nb_apps + a_index * nb_nodes + n_index
            indiv[key] = node_priority[n_index]

    return indiv


def create_individual_deadline(chromosome):
    """Create an individual that prioritizes request with strict response deadline
    """
    system = chromosome.system
    nb_apps = len(system.apps)
    nb_nodes = len(system.nodes)

    indiv = create_individual_empty(chromosome)
    max_deadline = 1.0

    for (a_index, app) in enumerate(system.apps):
        indiv[a_index] = 1.0
        deadline = app.deadline
        if deadline > max_deadline:
            max_deadline = deadline

    for (req_index, req) in enumerate(chromosome.requests):
        app_id, node_id = req
        key = nb_apps * (nb_nodes + 1) + req_index
        deadline = system.get_app(app_id).deadline
        value = 1.0 - deadline / float(max_deadline)
        indiv[key] = value

    return indiv


def invert_individual(chromosome, individual):
    """Invert a individual representation
    """
    indiv = individual[:chromosome.nb_genes]
    return list(map(lambda i: 1.0 - i, indiv))


def merge_population(chromosome, population, weights=None):
    """Merge a list of individuals into a single one
    """
    nb_genes = chromosome.nb_genes
    pop_size = len(population)
    if weights is None:
        weights = [1.0 / float(pop_size)] * pop_size

    merged_indiv = [0] * nb_genes
    for g in range(nb_genes):
        value = 0.0
        for i, indiv in enumerate(population):
            value += weights[i] * indiv[g]
        merged_indiv[g] = value

    return merged_indiv


def merge_creation_functions(chromosome, functions, weights=None):
    """Create an individual by merging the results of a list of creation functions
    """
    population = [f(chromosome) for f in functions]
    if len(population) > 1:
        return merge_population(chromosome, population, weights)
    elif len(population) > 0:
        return population[0]
    else:
        return None
