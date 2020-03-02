from statistics import mean


INF = float("inf")


def overall_migration_cost(system, solution):
    values = _calc_migration_cost(system, solution)
    return sum(values) if len(values) > 1 else 0.0


def max_migration_cost(system, solution):
    values = _calc_migration_cost(system, solution)
    return max(values) if len(values) > 1 else 0.0


def avg_migration_cost(system, solution):
    values = _calc_migration_cost(system, solution)
    return mean(values) if len(values) > 1 else 0.0


def _calc_migration_cost(system, solution):
    costs = []
    if system.control is not None:
        for app in system.apps:
            app_cost = 0.0

            for dst_node in system.nodes:
                prev_place = system.get_app_placement(app.id, dst_node.id)
                curr_place = solution.get_app_placement(app.id, dst_node.id)
                if not curr_place:
                    continue

                min_delay = INF
                for src_node in system.nodes:
                    if not system.get_app_placement(app.id, src_node.id):
                        continue

                    # TODO: get network delay of next time step
                    delay = system.get_net_delay(app.id, src_node.id, dst_node.id)
                    if delay < min_delay:
                        min_delay = delay

                app_cost += (1.0 - prev_place) * curr_place * min_delay * app.data_size

            costs.append(app_cost)
    return costs
