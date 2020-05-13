def filter_metric(metric_func, system, control_input, environment_input, apps_id=None, nodes_id=None):
    """Filter a metric for specified applications and nodes

    Args:
        metric_func (function): metric function
        system (sp.core.model.system.System): system
        control_input (sp.core.model.control_input.ControlInput): control input
        environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        apps_id (Union[list, int]): list of applications' id or a single application's id
        nodes_id (Union[list, int]): list of nodes' id or a single node's id
    Returns:
       float: metric value
    """
    filtered_system = system.filter(apps_id=apps_id, nodes_id=nodes_id)
    return metric_func(filtered_system, control_input, environment_input)
