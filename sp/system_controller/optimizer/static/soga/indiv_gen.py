from sp.core.heuristic.kmedoids import KMedoids
from sp.system_controller.utils import calc_load_before_distribution
from sp.core.heuristic.brkga import GAIndividual
import math


def create_empty_individual(ga_operator):
    """Create a default individual
    Args:
        ga_operator (SOGAOperator): genetic operator
    Returns:
        GAIndividual: encoded individual
    """
    chromosome = [0.0] * ga_operator.nb_genes
    return GAIndividual(chromosome)


def create_individual_cloud(ga_operator):
    """Create an individual that prioritizes the cloud node
    Args:
        ga_operator (SOGAOperator): genetic operator
    Returns:
        GAIndividual: encoded individual
    """
    chromosome = [0.0] * ga_operator.nb_genes
    return GAIndividual(chromosome)


def create_individual_net_delay(ga_operator):
    """Create an individual that prioritizes nodes having shorter avg. net delays to other nodes
    and requests with strict deadlines
    Args:
        ga_operator (SOGAOperator): genetic operator
    Returns:
        GAIndividual: encoded individual
    """
    system = ga_operator.system
    env_input = ga_operator.environment_input
    nb_apps = len(system.apps)
    nb_nodes = len(system.nodes)

    indiv = create_empty_individual(ga_operator)
    for (a_index, app) in enumerate(system.apps):
        indiv[a_index] = 1.0

        nodes_delay = []
        max_delay = 1.0
        for (dst_index, dst_node) in enumerate(system.nodes):
            avg_delay = 0.0
            count = 0
            for (src_index, src_node) in enumerate(system.nodes):
                avg_delay += env_input.get_net_delay(app.id, src_node.id, dst_node.id)
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


def create_individual_cluster_metoids(ga_operator, use_sc=False):
    """Create an individual based on k-medoids clustering.
    The idea is the users of an application are grouped and central nodes of each group are prioritized.
    It also prioritizes requests with strict deadlines
    Args:
        ga_operator (SOGAOperator): genetic operator
        use_sc (bool): whether to use the silhouette score method to find the number of clusters
    Returns:
        GAIndividual: encoded individual
    """
    system = ga_operator.system
    env_input = ga_operator.environment_input
    nb_apps = len(system.apps)
    nb_nodes = len(system.nodes)
    kmedoids = KMedoids()

    indiv = create_empty_individual(ga_operator)
    for (a_index, app) in enumerate(system.apps):
        indiv[a_index] = 1.0

        distances = [[float(env_input.get_net_delay(app.id, src_node.id, dst_node.id))
                      for dst_node in system.nodes]
                     for src_node in system.nodes]

        features = [n_index for (n_index, node) in enumerate(system.nodes)
                    if calc_load_before_distribution(app.id, node.id, system, env_input) > 0]

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


def create_individual_cluster_metoids_sc(ga_operator):
    """Create an individual based on k-medoids clustering with silhouette score.
    The idea is the users of an application are grouped and central nodes of each group are prioritized.
    It also prioritizes requests with strict deadlines
    Args:
        ga_operator (SOGAOperator): genetic operator
    Returns:
        GAIndividual: encoded individual
    """
    return create_individual_cluster_metoids(ga_operator, use_sc=True)


def create_individual_load(ga_operator):
    """Create an individual that prioritizes nodes with large load
    Args:
        ga_operator (SOGAOperator): genetic operator
    Returns:
        GAIndividual: encoded individual
    """
    system = ga_operator.system
    env_input = ga_operator.environment_input
    nb_apps = len(system.apps)
    nb_nodes = len(system.nodes)

    indiv = create_empty_individual(ga_operator)
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
            load = calc_load_before_distribution(app.id, node.id, system, env_input)
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

    for (req_index, req) in enumerate(ga_operator.requests):
        app_id, node_id = req
        key = nb_apps * (nb_nodes + 1) + req_index
        value = calc_load_before_distribution(app_id, node_id, system, env_input)
        if max_load > 0.0:
            value = value / float(max_load)
        indiv[key] = value

    return indiv


def create_individual_capacity(ga_operator):
    """Create an individual that prioritizes nodes with high capacity of resources
    Args:
        ga_operator (SOGAOperator): genetic operator
    Returns:
        GAIndividual: encoded individual
    """
    system = ga_operator.system
    nb_apps = len(system.apps)
    nb_nodes = len(system.nodes)
    nb_resources = len(system.resources)

    indiv = create_empty_individual(ga_operator)

    max_capacity = {r.name: 1.0 for r in system.resources}
    for (n_index, node) in enumerate(system.nodes):
        for resource in system.resources:
            capacity = node.capacity[resource.name]
            if capacity > max_capacity[resource.name] and not math.isinf(capacity):
                max_capacity[resource.name] = float(capacity)

    node_priority = [0.0 for _ in system.nodes]
    for (n_index, node) in enumerate(system.nodes):
        value = 0.0
        for resource in system.resources:
            capacity = node.capacity[resource.name]
            if math.isinf(capacity):
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


def create_individual_deadline(ga_operator):
    """Create an individual that prioritizes request with strict response deadline
    Args:
        ga_operator (SOGAOperator): genetic operator
    Returns:
        GAIndividual: encoded individual
    """
    system = ga_operator.system
    nb_apps = len(system.apps)
    nb_nodes = len(system.nodes)

    indiv = create_empty_individual(ga_operator)
    max_deadline = 1.0

    for (a_index, app) in enumerate(system.apps):
        indiv[a_index] = 1.0
        deadline = app.deadline
        if deadline > max_deadline:
            max_deadline = deadline

    for (req_index, req) in enumerate(ga_operator.requests):
        app_id, node_id = req
        key = nb_apps * (nb_nodes + 1) + req_index
        deadline = system.get_app(app_id).deadline
        value = 1.0 - deadline / float(max_deadline)
        indiv[key] = value

    return indiv


def invert_individual(ga_operator, individual):
    """Invert a individual representation
    Args:
        ga_operator (SOGAOperator): genetic operator
        individual (GAIndividual): encoded individual
    Returns:
        GAIndividual: inverted individual
    """
    chromosome = individual.chromosome
    inverted = list(map(lambda i: 1.0 - i, chromosome))
    return GAIndividual(chromosome)


def merge_population(ga_operator, population, weights=None):
    """Merge a list of individuals into a single one
    Args:
        ga_operator (SOGAOperator): genetic operator
        population (list(GAIndividual)): list of individuals
        weights (list): weight for each individual in the population
    Returns:
        GAIndividual: resulted individual
    """
    nb_genes = ga_operator.nb_genes
    pop_size = len(population)
    if weights is None:
        weights = [1.0 / float(pop_size)] * pop_size

    merged_indiv = create_empty_individual(ga_operator)
    for g in range(nb_genes):
        value = 0.0
        for (i, indiv) in enumerate(population):
            value += weights[i] * indiv[g]
        merged_indiv[g] = value

    return merged_indiv


def merge_creation_functions(ga_operator, functions, weights=None):
    """Create an individual by merging the results of a list of creation functions
    Args:
        ga_operator (SOGAOperator): genetic operator
        functions (list(function)): list of creation functions
        weights (list): weight for the individuals created by each function
    Returns:
        GAIndividual: resulted individual
    """
    population = [f(ga_operator) for f in functions]
    if len(population) > 1:
        return merge_population(ga_operator, population, weights)
    elif len(population) > 0:
        return population[0]
    else:
        return None
