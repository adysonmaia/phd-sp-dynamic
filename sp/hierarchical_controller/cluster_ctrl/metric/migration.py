from sp.hierarchical_controller.cluster_ctrl.model import ClusterSystem, ClusterControlInput, ClusterEnvironmentInput
from sp.hierarchical_controller.cluster_ctrl.util.calc import calc_min_migration_delay, calc_app_size
from statistics import mean


def overall_migration_cost(current_system, next_control, next_environment):
    """Overall Migration/Replication Cost Metric

    Args:
        current_system (ClusterSystem): current system's state
        next_control (ClusterControlInput): next control input
        next_environment (ClusterEnvironmentInput):  next environment input
    Returns:
        float: metric value
    """
    values = _calc_migration_cost(current_system, next_control, next_environment)
    return sum(values) if len(values) > 0 else 0.0


def max_migration_cost(current_system, next_control, next_environment):
    """Maximum Migration/Replication Cost Metric

    Args:
        current_system (ClusterSystem): current system's state
        next_control (ClusterControlInput): next control input
        next_environment (ClusterEnvironmentInput):  next environment input
    Returns:
        float: metric value
    """
    values = _calc_migration_cost(current_system, next_control, next_environment)
    return max(values) if len(values) > 0 else 0.0


def avg_migration_cost(current_system, next_control, next_environment):
    """Average Migration/Replication Cost Metric

    Args:
        current_system (ClusterSystem): current system's state
        next_control (ClusterControlInput): next control input
        next_environment (ClusterEnvironmentInput):  next environment input
    Returns:
        float: metric value
    """
    values = _calc_migration_cost(current_system, next_control, next_environment)
    return mean(values) if len(values) > 0 else 0.0


def migration_rate(current_system, next_control, next_environment):
    """Calculate the migration/replication ratio.
    That is, is fraction of new application replicas among all replicas

    Args:
        current_system (ClusterSystem): current system's state
        next_control (ClusterControlInput): next control input
        next_environment (ClusterEnvironmentInput):  next environment input
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

                total_place_count += int(next_place)
                new_place_count += int(next_place and not cur_place)

        if total_place_count > 0:
            ratio = new_place_count / float(total_place_count)

    return ratio


def weighted_migration_rate(current_system, next_control, next_environment):
    """Calculate the migration/replication ratio.
    That is, is fraction of new application replicas among all replicas

    Args:
        current_system (ClusterSystem): current system's state
        next_control (ClusterControlInput): next control input
        next_environment (ClusterEnvironmentInput):  next environment input
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
                app_size = calc_app_size(app.id, node.id, current_system, next_control, next_environment)

                total_place_count += int(next_place) * app_size
                new_place_count += int(next_place and not cur_place) * app_size

        if total_place_count > 0:
            ratio = new_place_count / float(total_place_count)

    return ratio


def _calc_migration_cost(current_system, next_control, next_environment):
    """Calculate migration/replication cost for every migrated/new application instance

    Args:
        current_system (ClusterSystem): current system's state
        next_control (ClusterControlInput): next control input
        next_environment (ClusterEnvironmentInput):  next environment input
    Returns:
        list: list of metric values
    """
    current_control = current_system.control_input
    costs = []
    if current_control is not None:
        for app in current_system.apps:
            # TODO: calculate only for internal nodes?
            for node in current_system.nodes:
                curr_place = current_control.get_app_placement(app.id, node.id)
                next_place = next_control.get_app_placement(app.id, node.id)
                if not next_place or curr_place:
                    continue

                delay = calc_min_migration_delay(app.id, node.id, current_system, next_control, next_environment)
                if delay > 0.0:
                    costs.append(delay)
    return costs
