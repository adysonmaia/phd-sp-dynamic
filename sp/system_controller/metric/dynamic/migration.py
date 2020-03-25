from statistics import mean
import math


def overall_migration_cost(current_system, next_control, next_environment):
    values = _calc_migration_cost(current_system, next_control, next_environment)
    return sum(values) if len(values) > 1 else 0.0


def max_migration_cost(current_system, next_control, next_environment):
    values = _calc_migration_cost(current_system, next_control, next_environment)
    return max(values) if len(values) > 1 else 0.0


def avg_migration_cost(current_system, next_control, next_environment):
    values = _calc_migration_cost(current_system, next_control, next_environment)
    return mean(values) if len(values) > 1 else 0.0


def _calc_migration_cost(current_system, next_control, next_environment):
    current_control = current_system.control_input
    costs = []
    if current_control is not None:
        for app in current_system.apps:
            app_cost = 0.0

            for dst_node in current_system.nodes:
                curr_place = current_control.get_app_placement(app.id, dst_node.id)
                next_place = next_control.get_app_placement(app.id, dst_node.id)
                if not next_place:
                    continue

                min_delay = math.inf
                for src_node in current_system.nodes:
                    if not current_control.get_app_placement(app.id, src_node.id):
                        continue

                    delay = next_environment.get_net_delay(app.id, src_node.id, dst_node.id)
                    if delay < min_delay:
                        min_delay = delay

                app_cost += (1.0 - curr_place) * next_place * min_delay * app.data_size

            costs.append(app_cost)
    return costs
