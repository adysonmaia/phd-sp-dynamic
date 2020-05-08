from sp.core.model import Resource
from sp.system_controller.util import calc_migration_delay
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
    current_control = current_system.control_input
    costs = []
    if current_control is not None:
        for app in current_system.apps:
            for node in current_system.nodes:
                curr_place = current_control.get_app_placement(app.id, node.id)
                next_place = next_control.get_app_placement(app.id, node.id)
                if not next_place or curr_place:
                    continue

                delay = calc_migration_delay(app.id, node.id, current_system, next_control, next_environment)
                if delay > 0.0:
                    costs.append(delay)
    return costs
