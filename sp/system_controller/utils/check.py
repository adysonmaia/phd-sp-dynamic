from sp.core.model import Resource
from sp.system_controller.utils.calc import calc_load_before_distribution
import math
import logging

ERROR_TOLERANCE = 0.001


def is_solution_valid(system, solution, environment_input):
    for app in system.apps:
        nb_instances = sum([solution.app_placement[app.id][n.id] for n in system.nodes])
        if nb_instances > app.max_instances or nb_instances == 0:
            logging.debug("Invalid number of instances for app %d: %d (max %d)",
                          app.id, nb_instances, app.max_instances)
            return False

        for src_node in system.nodes:
            src_ld = 0.0
            for dst_node in system.nodes:
                dst_ld = solution.load_distribution[app.id][src_node.id][dst_node.id]
                if math.isnan(dst_ld) or dst_ld < 0.0 or dst_ld > 1.0 + ERROR_TOLERANCE:
                    logging.debug("Invalid load distribution (app %d, src node %d, dst node %d): %f",
                                  app.id, src_node.id, dst_node.id, dst_ld)
                    return False

                if dst_ld > 0.0 and not solution.app_placement[app.id][dst_node.id]:
                    logging.debug("Invalid load distribution, node %d doesn't host the app %d",
                                  dst_node.id, app.id)
                    return False

                src_ld += dst_ld
            if abs(1.0 - src_ld) > ERROR_TOLERANCE:
                logging.debug("Invalid load distribution, "
                              "loads from node %d aren't completely distributed for app %d - %f",
                              src_node.id, app.id, src_ld)
                return False

    for dst_node in system.nodes:
        for resource in system.resources:
            allocated = 0.0
            for app in system.apps:
                alloc_res = solution.allocated_resource[app.id][dst_node.id][resource.name]
                if alloc_res > 0.0 and not solution.app_placement[app.id][dst_node.id]:
                    logging.debug("Invalid resource allocation for %s, node %d doesn't host app %d",
                                  resource.name, dst_node.id, app.id)
                    return False

                dst_load = 0.0
                for src_node in system.nodes:
                    ld = solution.load_distribution[app.id][src_node.id][dst_node.id]
                    src_load = calc_load_before_distribution(app.id, src_node.id, system, environment_input)
                    dst_load += float(ld * src_load)

                received_load = solution.received_load[app.id][dst_node.id]
                if abs(dst_load - received_load) > ERROR_TOLERANCE:
                    logging.debug("Invalid received load of node %d for app %d: %f (valid %f)",
                                  dst_node.id, app.id, received_load, dst_load)
                    return False

                if dst_load > 0.0:
                    if not solution.app_placement[app.id][dst_node.id]:
                        logging.debug("Invalid received load, node %d doesn't host app %d: %f",
                                      dst_node.id, app.id, dst_load)
                        return False

                    app_demand = app.demand[resource.name](dst_load)
                    if abs(app_demand - alloc_res) > ERROR_TOLERANCE:
                        logging.debug("Invalid allocated resource for (app %d, node %d, resource %s): %f (valid %f)",
                                      app.id, dst_node.id, resource.name, alloc_res, app_demand)
                        return False

                    allocated += app_demand

            capacity = dst_node.capacity[resource.name]
            if allocated - capacity > ERROR_TOLERANCE:
                logging.debug("Invalid allocated resource, capacity exceeded for resource %s in node %d: %f (max %f)",
                              resource.name, dst_node.id, allocated, capacity)
                return False

    for app in system.apps:
        for dst_node in system.nodes:
            if not solution.get_app_placement(app.id, dst_node.id):
                continue

            arrival_rate = 0.0
            for src_node in system.nodes:
                ld = solution.load_distribution[app.id][src_node.id][dst_node.id]
                src_load = calc_load_before_distribution(app.id, src_node.id, system, environment_input)
                arrival_rate += float(ld * src_load)

            alloc_cpu = solution.allocated_resource[app.id][dst_node.id][Resource.CPU]
            service_rate = alloc_cpu / float(app.work_size)

            if arrival_rate - service_rate > ERROR_TOLERANCE:
                logging.debug("Invalid processing queue in node %d for app %d, "
                              "arrival rate %f exceeds service rate %f",
                              dst_node.id, app.id, arrival_rate, service_rate)
                return False

    return True
