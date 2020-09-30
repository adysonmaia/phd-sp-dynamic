from sp.core.heuristic.kmedoids import KMedoids
from sp.core.heuristic.brkga import GAIndividual, GAOperator
from sp.system_controller.optimizer.soga.indiv_gen import create_empty_individual, invert_individual
from sp.system_controller.optimizer.soga.indiv_gen import merge_population, merge_creation_functions
from sp.hierarchical_controller.global_ctrl.util.calc import calc_load_before_distribution
from .ga_operator import GlobalMOGAOperator
import math


def create_individual_cloud(ga_operator):
    """Create an individual that prioritizes the cloud node

    Args:
        ga_operator (GlobalMOGAOperator): genetic operator
    Returns:
        GAIndividual: encoded individual
    """
    chromosome = [0.0] * ga_operator.nb_genes
    return GAIndividual(chromosome)


def create_individual_current(ga_operator):
    """Create an individual based on current state and control input

    Args:
        ga_operator (GlobalMOGAOperator): genetic operator
    Returns:
        GAIndividual: encoded individual
    """
    indiv = create_empty_individual(ga_operator)
    system = ga_operator.system
    control_input = system.control_input
    nb_apps = len(system.apps)
    nb_nodes = len(system.nodes)
    nb_real_nodes = len(system.real_nodes)

    if control_input is not None:
        for (a_index, app) in enumerate(system.apps):
            place_count = 0
            node_count = 0
            for (dst_index, dst_node) in enumerate(system.nodes):
                key = 2 * nb_apps + a_index * nb_nodes + dst_index
                key_2 = key + nb_apps * nb_nodes
                value = int(control_input.get_app_placement(app.id, dst_node.id))
                place_count += value
                if value > 0:
                    node_count += 1
                    indiv[key] = 1.0
                indiv[key_2] = value

            max_instances = min(nb_real_nodes, app.max_instances)
            indiv[a_index] = place_count / float(max_instances) if max_instances > 0 else 1.0
            indiv[nb_apps + a_index] = node_count / float(nb_nodes) if nb_nodes > 0 else 1.0

            for (dst_index, dst_node) in enumerate(system.nodes):
                key = nb_apps * (2 + nb_nodes) + a_index * nb_nodes + dst_index
                value = indiv[key] / float(place_count) if place_count > 0 else 1.0
                indiv[key] = value

    return indiv


def create_individual_net_delay(ga_operator):
    """Create an individual that prioritizes nodes having shorter avg. net delays to other nodes

    Args:
        ga_operator (GlobalMOGAOperator): genetic operator
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
        indiv[nb_apps + a_index] = 1.0

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
            key = 2 * nb_apps + a_index * nb_nodes + dst_index
            value = 1.0 - nodes_delay[dst_index] / float(max_delay)
            indiv[key] = value

            key_2 = key + nb_apps * nb_nodes
            indiv[key_2] = 1.0

    return indiv


def create_individual_load(ga_operator):
    """Create an individual that prioritizes nodes with large load

    Args:
        ga_operator (GlobalMOGAOperator): genetic operator
    Returns:
        GAIndividual: encoded individual
    """
    system = ga_operator.system
    env_input = ga_operator.environment_input
    nb_apps = len(system.apps)
    nb_nodes = len(system.nodes)

    indiv = create_empty_individual(ga_operator)
    max_load = 0.0

    for (a_index, app) in enumerate(system.apps):
        indiv[a_index] = 1.0
        indiv[nb_apps + a_index] = 1.0

        max_app_load = 0.0
        for (n_index, node) in enumerate(system.nodes):
            key = 2 * nb_apps + a_index * nb_nodes + n_index
            key_2 = key + nb_apps * nb_nodes
            load = calc_load_before_distribution(app.id, node.id, system, env_input)
            value = load
            indiv[key] = value
            indiv[key_2] = value
            if load > max_app_load:
                max_app_load = load
            if load > max_load:
                max_load = load

        if max_app_load > 0.0:
            for (n_index, node) in enumerate(system.nodes):
                key = 2 * nb_apps + a_index * nb_nodes + n_index
                key_2 = key + nb_apps * nb_nodes
                value = indiv[key] / float(max_app_load)
                indiv[key] = value
                indiv[key_2] = value

    for (req_index, req) in enumerate(ga_operator.requests):
        app_id, node_id = req
        key = 2 * nb_apps * (1 + nb_nodes) + req_index
        value = calc_load_before_distribution(app_id, node_id, system, env_input)
        if max_load > 0.0:
            value = value / float(max_load)
        indiv[key] = value

    return indiv


def create_individual_capacity(ga_operator):
    """Create an individual that prioritizes nodes with high capacity of resources

    Args:
        ga_operator (GlobalMOGAOperator): genetic operator
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
            capacity = node.capacity[resource.name] * len(node.nodes)
            if capacity > max_capacity[resource.name] and not math.isinf(capacity):
                max_capacity[resource.name] = float(capacity)

    node_priority = [0.0 for _ in system.nodes]
    for (n_index, node) in enumerate(system.nodes):
        value = 0.0
        for resource in system.resources:
            capacity = node.capacity[resource.name] * len(node.nodes)
            if math.isinf(capacity):
                value += 1.0
            else:
                value += capacity / max_capacity[resource.name]
        value = value / float(nb_resources)
        node_priority[n_index] = value

    for (a_index, app) in enumerate(system.apps):
        indiv[a_index] = 1.0
        indiv[nb_apps + a_index] = 1.0
        for (n_index, node) in enumerate(system.nodes):
            key = 2 * nb_apps + a_index * nb_nodes + n_index
            key_2 = key + nb_apps * nb_nodes
            indiv[key] = node_priority[n_index]
            indiv[key_2] = 1.0

    return indiv


def create_individual_deadline(ga_operator):
    """Create an individual that prioritizes request with strict response deadline

    Args:
        ga_operator (GlobalMOGAOperator): genetic operator
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
        indiv[nb_apps + a_index] = 1.0
        deadline = app.deadline
        if deadline > max_deadline:
            max_deadline = deadline

    for (req_index, req) in enumerate(ga_operator.requests):
        app_id, node_id = req
        key = 2 * nb_apps * (1 + nb_nodes) + req_index
        deadline = system.get_app(app_id).deadline
        value = 1.0 - deadline / float(max_deadline)
        indiv[key] = value

    return indiv
