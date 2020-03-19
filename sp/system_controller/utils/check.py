from sp.core.model import Resource
from sp.system_controller.utils.calc import calc_load_before_distribution
import math

ERROR_TOLERANCE = 0.001


def is_solution_valid(system, solution, environment_input):
    for app in system.apps:
        nb_instances = sum([solution.app_placement[app.id][n.id] for n in system.nodes])
        if nb_instances > app.max_instances or nb_instances == 0:
            print("\nA")
            print(nb_instances, app.max_instances)
            return False

        for src_node in system.nodes:
            src_ld = 0.0
            for dst_node in system.nodes:
                dst_ld = solution.load_distribution[app.id][src_node.id][dst_node.id]
                if math.isnan(dst_ld) or dst_ld < 0.0 or dst_ld > 1.0 + ERROR_TOLERANCE:
                    print("\nB")
                    return False

                if dst_ld > 0.0 and not solution.app_placement[app.id][dst_node.id]:
                    print("\nC")
                    return False

                src_ld += dst_ld
            if abs(1.0 - src_ld) > ERROR_TOLERANCE:
                print("\nD")
                return False

    for dst_node in system.nodes:
        for resource in system.resources:
            allocated = 0.0
            for app in system.apps:
                dst_load = 0.0
                for src_node in system.nodes:
                    ld = solution.load_distribution[app.id][src_node.id][dst_node.id]
                    src_load = calc_load_before_distribution(app.id, src_node.id, system, environment_input)
                    dst_load += float(ld * src_load)

                received_load = solution.received_load[app.id][dst_node.id]
                if abs(dst_load - received_load) > ERROR_TOLERANCE:
                    print("\nE")
                    print(dst_load, received_load)
                    return False

                if dst_load > 0.0:
                    if not solution.app_placement[app.id][dst_node.id]:
                        print("\nF")
                        print(dst_load)
                        return False

                    app_demand = app.demand[resource.name](dst_load)
                    app_demand_2 = app.demand[resource.name](received_load)
                    alloc_res = solution.allocated_resource[app.id][dst_node.id][resource.name]
                    if abs(app_demand - alloc_res) > ERROR_TOLERANCE:
                        print("\nG")
                        print(app_demand, alloc_res, app_demand_2)
                        return False

                    allocated += app_demand

            capacity = dst_node.capacity[resource.name]
            if allocated - capacity > ERROR_TOLERANCE:
                print("\nH")
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
                print("\nI")
                return False

    return True
