from .iter_coop import IterativeCooperation
import math


class NoCooperation(IterativeCooperation):
    """No Cooperative LLC Algorithm

    """

    def __init__(self,
                 objective,
                 ga_params,
                 ga_operator_class,
                 ga_operator_params,
                 pool_size=0):
        """Initialization
        """
        IterativeCooperation.__init__(self,
                                      objective=objective,
                                      ga_params=ga_params,
                                      ga_operator_class=ga_operator_class,
                                      ga_operator_params=ga_operator_params,
                                      max_iteration=0,
                                      pool_size=pool_size)

    def _init_ext_info(self):
        """Initialize information about external external nodes of each cluster
        """
        IterativeCooperation._init_ext_info(self)

        for node in self._global_scenario.network.nodes:
            system = self._cluster_systems[node.id][0]
            for time_step in range(self.control_sequence_length):
                ctrl_limit = self._cluster_ctrl_limits[node.id][time_step]
                env_input = self._cluster_env_inputs[node.id][time_step]

                for app in system.apps:
                    for ext_node in self._global_scenario.network.nodes:
                        if node == ext_node:
                            continue

                        max_dispatch_load = 0.0
                        if ext_node.is_cloud():
                            max_dispatch_load = math.inf
                        ctrl_limit.max_dispatch_load[app.id][ext_node.id] = max_dispatch_load

                        env_input.generated_load[app.id][ext_node.id] = 0.0
                        env_input.additional_received_load[app.id][ext_node.id] = 0.0
                        env_input.nb_instances[app.id][ext_node.id] = 0
                        if self._global_control_input is not None:
                            nb_instances = self._global_control_input.get_max_app_placement(app.id, ext_node.id)
                            env_input.nb_instances[app.id][ext_node.id] = nb_instances

