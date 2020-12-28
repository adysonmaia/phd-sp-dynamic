def filter_metric(metric_func, system, control_input, environment_input,
                  apps_id=None, nodes_id=None, users_id=None, apps_type=None, nodes_type=None):
    """Filter a metric for the specified applications and nodes

    Args:
        metric_func: metric function
        system (sp.core.model.system.System): system
        control_input (sp.core.model.control_input.ControlInput): control input
        environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        apps_id (Union[list, int]): list of applications' id or a single application's id
        nodes_id (Union[list, int]): list of nodes' id or a single node's id
        users_id (Union[list, int]): list of users' id or a single user's id
        apps_type (Union[list, str]): list of applications' type or a single application's type
        nodes_type (Union[list, str]): list of nodes' type or a single node's type
    Returns:
       float: metric value
    """
    filtered_system = system.filter(apps_id=apps_id, nodes_id=nodes_id, users_id=users_id,
                                    apps_type=apps_type, nodes_type=nodes_type)
    return metric_func(filtered_system, control_input, environment_input)
