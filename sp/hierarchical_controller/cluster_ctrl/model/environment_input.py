from sp.core.model import EnvironmentInput, System, ControlInput
from sp.system_controller.util.calc import calc_load_after_distribution, calc_received_load
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalNode
from collections import defaultdict
import math


class ClusterEnvironmentInput(EnvironmentInput):
    """Cluster Environment Input Model Class

    """

    def __init__(self):
        """Initialisation
        """
        EnvironmentInput.__init__(self)
        self.additional_received_load = defaultdict(lambda: defaultdict(float))
        self.nb_instances = defaultdict(lambda: defaultdict(int))

    def __copy__(self):
        """Shallow copy

        Returns:
            ClusterEnvironmentInput: the shallow copy
        """
        cp = EnvironmentInput.__copy__(self)
        cp.additional_received_load = self.additional_received_load
        cp.nb_instances = self.nb_instances
        return cp

    def get_additional_received_load(self, app_id, node_id):
        """Get the additional received load of an external cluster.
        This is the load from other clusters to am external cluster

        Args:
            app_id (int): application's id
            node_id (int): cluster's id

        Returns:
            float: arrival rate
        """
        return self.additional_received_load[app_id][node_id]

    def get_nb_instances(self, app_id, node_id):
        """Get number of application's instances running in an external cluster

        Args:
            app_id (int): application's id
            node_id (int): cluster's id

        Returns:
            int: number of instances
        """
        return self.nb_instances[app_id][node_id]

    @staticmethod
    def from_real_environment_input(environment_input, global_scenario, global_node, system=None, control_input=None):
        """Create cluster environment input from real environment input

        Args:
            environment_input (EnvironmentInput): real environment input
            global_scenario (GlobalScenario): global scenario
            global_node (GlobalNode): global node as the cluster
            system (System): real system
            control_input (ControlInput): real control input

        Returns:
            ClusterEnvironmentInput: cluster environment input
        """
        return from_real_environment_input(environment_input, global_scenario, global_node, system, control_input)


def from_real_environment_input(environment_input, global_scenario, global_node, system=None, control_input=None):
    """Create cluster environment input from real environment input

    Args:
        environment_input (EnvironmentInput): real environment input
        global_scenario (GlobalScenario): global scenario
        global_node (GlobalNode): global node as the cluster
        system (System): real system
        control_input (ControlInput): real control input

    Returns:
        ClusterEnvironmentInput: cluster environment input
    """
    c_env_input = ClusterEnvironmentInput()
    real_scenario = global_scenario.real_scenario

    external_nodes = [ext_node for ext_node in global_scenario.network.nodes if ext_node != global_node]
    all_nodes = external_nodes + global_node.nodes

    # Initialization
    for app in real_scenario.apps:
        c_env_input.generated_load[app.id] = {}
        c_env_input.net_delay[app.id] = {}
        c_env_input.net_path[app.id] = {}
        for node in all_nodes:
            c_env_input.generated_load[app.id][node.id] = 0.0
            c_env_input.net_delay[app.id][node.id] = {}
            c_env_input.net_path[app.id][node.id] = {}
            for dst_node in all_nodes:
                c_env_input.net_delay[app.id][node.id][dst_node.id] = math.inf
                c_env_input.net_path[app.id][node.id][dst_node.id] = None

    for app in real_scenario.apps:
        # For nodes inside the cluster
        for real_node in global_node.nodes:
            # Generated load
            load = environment_input.generated_load[app.id][real_node.id]
            c_env_input.generated_load[app.id][real_node.id] = load

            # Network information between nodes inside the cluster
            for real_dst_node in global_node.nodes:
                delay = environment_input.net_delay[app.id][real_node.id][real_dst_node.id]
                net_path = environment_input.net_path[app.id][real_node.id][real_dst_node.id]
                c_env_input.net_delay[app.id][real_node.id][real_dst_node.id] = delay
                c_env_input.net_path[app.id][real_node.id][real_dst_node.id] = net_path

            # Network information between nodes in the cluster and external clusters
            for ext_node in external_nodes:
                real_dst_node = ext_node.central_node
                delay = environment_input.net_delay[app.id][real_node.id][real_dst_node.id]
                net_path = environment_input.net_path[app.id][real_node.id][real_dst_node.id]
                c_env_input.net_delay[app.id][real_node.id][ext_node.id] = delay
                c_env_input.net_path[app.id][real_node.id][ext_node.id] = net_path

        # For nodes outside the cluster
        for ext_node in external_nodes:
            real_src_node = ext_node.central_node

            # Network information between nodes in the cluster and external clusters
            for real_dst_node in global_node.nodes:
                delay = environment_input.net_delay[app.id][real_src_node.id][real_dst_node.id]
                net_path = environment_input.net_path[app.id][real_src_node.id][real_dst_node.id]
                c_env_input.net_delay[app.id][ext_node.id][real_dst_node.id] = delay
                c_env_input.net_path[app.id][ext_node.id][real_dst_node.id] = net_path

            # Network information between external clusters
            for ext_dst_node in external_nodes:
                real_dst_node = ext_dst_node.central_node
                delay = environment_input.net_delay[app.id][real_src_node.id][real_dst_node.id]
                net_path = environment_input.net_path[app.id][real_src_node.id][real_dst_node.id]
                c_env_input.net_delay[app.id][ext_node.id][ext_dst_node.id] = delay
                c_env_input.net_path[app.id][ext_node.id][ext_dst_node.id] = net_path

    if system is not None and control_input is not None:
        for app in real_scenario.apps:
            for ext_node in external_nodes:
                # load dispatched from external nodes to the cluster is the generated load of these external nodes
                load = 0.0
                for real_src_node in ext_node.nodes:
                    for real_dst_node in global_node.nodes:
                        load += calc_load_after_distribution(app.id, real_src_node.id, real_dst_node.id,
                                                             system, control_input, environment_input)
                c_env_input.generated_load[app.id][ext_node.id] = load

                # Number of instances and additional received load
                place_count = 0
                total_load = 0.0
                cluster_load = 0.0

                for real_node in ext_node.nodes:
                    place_count += int(control_input.get_app_placement(app.id, real_node.id))
                    total_load += calc_received_load(app.id, real_node.id, system, control_input, environment_input)
                for real_src_node in global_node.nodes:
                    for real_dst_node in ext_node.nodes:
                        cluster_load += calc_load_after_distribution(app.id, real_src_node.id, real_dst_node.id,
                                                                     system, control_input, environment_input)
                additional_load = 0.0
                if place_count > 0:
                    additional_load = min(0.0, total_load - cluster_load) / float(place_count)
                c_env_input.nb_instances[app.id][ext_node.id] = place_count
                c_env_input.additional_received_load[app.id][ext_node.id] = additional_load

    return c_env_input

