from sp.hierarchical_controller.global_ctrl.model import GlobalSystem, GlobalControlInput, GlobalEnvironmentInput
from sp.hierarchical_controller.global_ctrl.util.calc import calc_min_migration_delay, calc_app_size
from statistics import mean


def overall_migration_cost(current_system, next_control, next_environment):
    """Overall Migration/Replication Cost Metric

    Args:
        current_system (GlobalSystem): current system's state
        next_control (GlobalControlInput): next control input
        next_environment (GlobalEnvironmentInput):  next environment input
    Returns:
        float: metric value
    """
    values = _calc_migration_cost(current_system, next_control, next_environment)
    return sum(values) if len(values) > 0 else 0.0


def max_migration_cost(current_system, next_control, next_environment):
    """Maximum Migration/Replication Cost Metric

    Args:
        current_system (GlobalSystem): current system's state
        next_control (GlobalControlInput): next control input
        next_environment (GlobalEnvironmentInput):  next environment input
    Returns:
        float: metric value
    """
    values = _calc_migration_cost(current_system, next_control, next_environment)
    return max(values) if len(values) > 0 else 0.0


def avg_migration_cost(current_system, next_control, next_environment):
    """Average Migration/Replication Cost Metric

    Args:
        current_system (GlobalSystem): current system's state
        next_control (GlobalControlInput): next control input
        next_environment (GlobalEnvironmentInput):  next environment input
    Returns:
        float: metric value
    """
    values = _calc_migration_cost(current_system, next_control, next_environment)
    return mean(values) if len(values) > 0 else 0.0


def migration_rate(current_system, next_control, next_environment):
    """Calculate the migration/replication ratio.
    That is, is fraction of new application replicas among all replicas

    Args:
        current_system (GlobalSystem): current system's state
        next_control (GlobalControlInput): next control input
        next_environment (GlobalEnvironmentInput):  next environment input
    Returns:
        float: metric value
    """
    ratio = 0.0
    current_control = current_system.control_input
    if current_control is not None:
        new_place_count = 0
        total_place_count = 0
        for app in current_system.apps:
            for node in current_system.nodes:
                cur_place = current_control.get_app_placement(app.id, node.id)
                next_place = next_control.get_app_placement(app.id, node.id)
                delta_place = next_place - cur_place

                total_place_count += next_place
                new_place_count += int(max(0, delta_place))

        if total_place_count > 0:
            ratio = new_place_count / float(total_place_count)

    return ratio


def weighted_migration_rate(current_system, next_control, next_environment):
    """Calculate the migration/replication ratio.
    That is, is fraction of new application replicas among all replicas

    Args:
        current_system (GlobalSystem): current system's state
        next_control (GlobalControlInput): next control input
        next_environment (GlobalEnvironmentInput):  next environment input
    Returns:
        float: metric value
    """
    ratio = 0.0
    current_control = current_system.control_input
    if current_control is not None:
        new_place_count = 0
        total_place_count = 0
        for app in current_system.apps:
            for node in current_system.nodes:
                cur_place = current_control.get_app_placement(app.id, node.id)
                next_place = next_control.get_app_placement(app.id, node.id)
                delta_place = next_place - cur_place
                app_size = calc_app_size(app.id, node.id, current_system, next_control, next_environment)

                total_place_count += next_place * app_size
                new_place_count += max(0, delta_place) * app_size

        if total_place_count > 0:
            ratio = new_place_count / float(total_place_count)

    return ratio


def _calc_migration_cost(current_system, next_control, next_environment):
    """Calculate migration/replication cost for every migrated/new application instance

    Args:
        current_system (GlobalSystem): current system's state
        next_control (GlobalControlInput): next control input
        next_environment (GlobalEnvironmentInput):  next environment input
    Returns:
        list: list of metric values
    """
    current_control = current_system.control_input
    costs = []
    if current_control is not None:
        for app in current_system.apps:
            for node in current_system.nodes:
                curr_place = current_control.get_app_placement(app.id, node.id)
                next_place = next_control.get_app_placement(app.id, node.id)
                delta_place = next_place - curr_place
                if delta_place <= 0:
                    continue

                delay = calc_min_migration_delay(app.id, node.id, current_system, next_control, next_environment)
                if delay > 0.0:
                    costs.append(delay)
    return costs
