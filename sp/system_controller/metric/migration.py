from sp.core.model import Resource
from sp.system_controller.util import calc_initialization_delay
from statistics import mean
import math


def overall_migration_cost(current_system, next_control, next_environment):
    values = _calc_migration_cost(current_system, next_control, next_environment)
    return sum(values) if len(values) > 0 else 0.0


def max_migration_cost(current_system, next_control, next_environment):
    values = _calc_migration_cost(current_system, next_control, next_environment)
    return max(values) if len(values) > 0 else 0.0


def avg_migration_cost(current_system, next_control, next_environment):
    values = _calc_migration_cost(current_system, next_control, next_environment)
    return mean(values) if len(values) > 0 else 0.0


def _calc_migration_cost(current_system, next_control, next_environment):
    costs = []
    for app in current_system.apps:
        for node in current_system.nodes:
            delay = calc_initialization_delay(app.id, node.id, current_system, next_control, next_environment)
            if delay > 0.0:
                costs.append(delay)
    return costs

    # current_control = current_system.control_input
    # costs = []
    # if current_control is not None:
    #     for app in current_system.apps:
    #         for dst_node in current_system.nodes:
    #             curr_place = current_control.get_app_placement(app.id, dst_node.id)
    #             next_place = next_control.get_app_placement(app.id, dst_node.id)
    #             if not next_place or curr_place:
    #                 continue
    #
    #             min_delay = math.inf
    #             selected_node = current_system.cloud_node
    #             for src_node in current_system.nodes:
    #                 if not current_control.get_app_placement(app.id, src_node.id):
    #                     continue
    #
    #                 delay = next_environment.get_net_delay(app.id, src_node.id, dst_node.id)
    #                 if delay < min_delay:
    #                     min_delay = delay
    #                     selected_node = src_node
    #
    #             app_size = 0.0
    #             for resource_name in [Resource.RAM, Resource.DISK]:
    #                 if resource_name in current_system.resources_name:
    #                     app_size += current_control.get_allocated_resource(app.id, selected_node.id, resource_name)
    #             app_size *= 8.0
    #             costs.append(app_size)
    # return costs
