from sp.system_controller.util import calc_response_time, calc_load_after_distribution
from statistics import mean


def max_response_time(system, control_input, environment_input):
    rt = _calc_rt(system, control_input, environment_input)
    return max(rt) if len(rt) > 0 else 0.0


def avg_response_time(system, control_input, environment_input):
    rt = _calc_rt(system, control_input, environment_input)
    return mean(rt) if len(rt) > 0 else 0.0


def overall_response_time(system, control_input, environment_input):
    rt = _calc_rt(system, control_input, environment_input)
    return sum(rt) if len(rt) > 0 else 0.0


def _calc_rt(system, control_input, environment_input):
    list_rt = []
    for app in system.apps:
        for dst_node in system.nodes:
            if not control_input.get_app_placement(app.id, dst_node.id):
                continue
            for src_node in system.nodes:
                load = calc_load_after_distribution(app.id, src_node.id, dst_node.id,
                                                    system, control_input, environment_input)
                if load > 0.0:
                    rt = calc_response_time(app.id, src_node.id, dst_node.id,
                                            system, control_input, environment_input)
                    list_rt.append(rt)
    return list_rt
