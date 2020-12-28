from sp.core.heuristic.nsgaii import NSGAII
from sp.core.model import System, ControlInput, EnvironmentInput
from sp.system_controller.util import pareto_dominates, preferred_dominates
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalControlInput
from sp.hierarchical_controller.cluster_ctrl.model import ClusterSystem, ClusterControlInput, ClusterEnvironmentInput
from sp.hierarchical_controller.cluster_ctrl.model import ClusterControlLimit
from sp.hierarchical_controller.cluster_ctrl.estimator import ClusterSystemEstimator
from sp.hierarchical_controller.cluster_ctrl.util.calc import calc_load_after_distribution, calc_received_load
from sp.hierarchical_controller.cluster_ctrl.util.calc import calc_load_before_distribution
from sp.hierarchical_controller.cluster_ctrl.util.make import make_real_control_input
import copy
import math

from multiprocessing.dummy import Pool as ThreadPool
import multiprocessing as mp


_GA_PARAMS = {
    "nb_generations": 100,
    "population_size": 100,
    "elite_proportion": 0.1,
    "mutant_proportion": 0.1,
    "elite_probability": 0.6,
    "stop_threshold": 0.10,
    "timeout": None,
    "pool_size": 4,
    "dominance_func": preferred_dominates,
}

_GA_OPERATOR_PARAMS = {
    "load_chunk_distribution": None,
    "objective_aggregator": sum,
}


class IterativeCooperation:
    """Iterative Cooperation LLC Algorithm

    Attributes:
        objective (list): list of objective functions
        ga_params (dict): genetic algorithm parameters
        ga_operator_class: ga operator class
        ga_operator_params (dict): ga operator parameters
        max_iteration (int): max. algorithm iteration
        pool_size (int): multi-thread pool size
        monitor (sp.simulator.monitor.monitor.Monitor): simulator's monitor
    """

    def __init__(self,
                 objective,
                 ga_params,
                 ga_operator_class,
                 ga_operator_params,
                 max_iteration=1,
                 pool_size=0,
                 monitor=None):
        """Initialization
        """
        self.objective = objective
        self.ga_params = ga_params
        self.ga_operator_class = ga_operator_class
        self.ga_operator_params = ga_operator_params
        self.max_iteration = int(max(1, max_iteration))
        self.pool_size = pool_size
        self.monitor = monitor

        self._real_system = None
        self._real_environment_inputs = None
        self._global_control_input = None
        self._global_scenario = None

        self._system_estimator = ClusterSystemEstimator()

        self._cluster_systems = None
        self._cluster_env_inputs = None
        self._cluster_ctrl_inputs = None
        self._cluster_ctrl_limits = None
        self._cluster_last_population = None

    def init_params(self):
        """Initialize parameters for a simulation
        """
        self._cluster_last_population = {}

    def clear_params(self):
        """Clear parameters of a simulation
        """
        self._cluster_last_population = None

    @property
    def control_sequence_length(self):
        """Control sequence length

        Returns:
            int: length
        """
        return len(self._real_environment_inputs)

    def solve(self, system, environment_inputs, global_scenario, global_control_input):
        """Solve service placement problem

        Args:
            system (System): current real system's state
            environment_inputs (list(EnvironmentInput)): predicted real environment inputs
            global_scenario (GlobalScenario): global scenario
            global_control_input (GlobalControlInput): global control input

        Returns:
            ControlInput: solution as a real control input
        """
        self._set_cluster_params(system, environment_inputs, global_scenario, global_control_input)

        map_func = map
        pool_size = int(min(self.pool_size, mp.cpu_count(), len(self._global_scenario.network.nodes)))
        pool = None
        if pool_size > 1:
            try:
                pool = ThreadPool(pool_size)
                map_func = pool.map
            except ValueError:
                pass

        for it in range(self.max_iteration):
            result = list(map_func(self._solver_for_cluster, self._global_scenario.network.nodes_id))
            self._update_ext_info()

        ctrl_inputs = {n.id: self._cluster_ctrl_inputs[n.id][0] for n in self._global_scenario.network.nodes}
        real_ctrl_input = make_real_control_input(system, environment_inputs[0], ctrl_inputs, global_scenario)

        return real_ctrl_input

    def _solver_for_cluster(self, cluster_id, iteration=None):
        """

        Args:
            cluster_id (int): cluster's id
            iteration (int): iteration
        Returns:

        """
        if self.monitor is not None:
            self.monitor("on_cluster_ctrl_started", self._real_system.time, cluster_id=cluster_id)

        ga_params = copy.copy(_GA_PARAMS)
        if isinstance(self.ga_params, dict):
            ga_params.update(self.ga_params)

        ga_operator_params = copy.copy(_GA_OPERATOR_PARAMS)
        if isinstance(self.ga_operator_params, dict):
            ga_operator_params.update(self.ga_operator_params)

        cluster_system = self._cluster_systems[cluster_id][0]
        cluster_env_inputs = self._cluster_env_inputs[cluster_id]
        cluster_ctrl_limits = self._cluster_ctrl_limits[cluster_id]
        cluster_last_population = None
        if cluster_id in self._cluster_last_population:
            cluster_last_population = self._cluster_last_population[cluster_id]

        ga_operator = self.ga_operator_class(objective=self.objective,
                                             system=cluster_system,
                                             environment_inputs=cluster_env_inputs,
                                             control_limits=cluster_ctrl_limits,
                                             system_estimator=self._system_estimator,
                                             extra_first_population=cluster_last_population,
                                             **ga_operator_params)

        ga = NSGAII(operator=ga_operator, **ga_params)
        population = ga.solve()
        best_individual = population[0]
        ctrl_sequence, system_sequence = ga_operator.decode(best_individual)

        # from sp.hierarchical_controller.cluster_ctrl.util import calc as cluster_calc
        # # from sp.system_controller.util import calc as cluster_calc
        # ctrl_input = ctrl_sequence[0]
        # ctrl_limit = cluster_ctrl_limits[0]
        # env_input = cluster_env_inputs[0]
        # for app in cluster_system.apps:
        #     for ext_node in cluster_system.external_nodes:
        #         max_load = ctrl_limit.get_max_dispatch_load(app.id, ext_node.id)
        #         # nb_instance = env_input.get_nb_instances(app.id, ext_node.id)
        #         # init_load = env_input.get_additional_received_load(app.id, ext_node.id)
        #         # load = ctrl_input.get_received_load(app.id, ext_node.id)
        #         # print("iter", it, global_node.id, ext_node.id, app.id, nb_instance, init_load, load, max_load)
        #         # if nb_instance * (load - init_load) > max_load:
        #         #     print("test", app.id, global_node.id, ext_node.id, load, max_load)
        #
        #         load = 0.0
        #         for int_node in cluster_system.internal_nodes:
        #             load += cluster_calc.calc_load_after_distribution(app.id, int_node.id, ext_node.id,
        #                                                               cluster_system, ctrl_input, env_input,
        #                                                               per_instance=False)
        #         if load > max_load:
        #             print("iter", iteration, cluster_id, ext_node.id, app.id, load, max_load)

        self._cluster_ctrl_inputs[cluster_id] = ctrl_sequence
        self._cluster_systems[cluster_id] = system_sequence
        self._cluster_last_population[cluster_id] = population

        if self.monitor is not None:
            self.monitor("on_cluster_ctrl_ended", self._real_system.time,
                         cluster_id=cluster_id,
                         system=cluster_system, environment_input=cluster_env_inputs[0],
                         control_input=ctrl_sequence[0])

        return cluster_id

    def _set_cluster_params(self, system, environment_inputs, global_scenario, global_control_input):
        """Set clusters' parameters

        Args:
            system (System): current real system's state
            environment_inputs (list(EnvironmentInput)): predicted real environment inputs
            global_scenario (GlobalScenario): global scenario
            global_control_input (GlobalControlInput): global control input
        """
        self._real_system = system
        self._real_environment_inputs = environment_inputs
        self._global_control_input = global_control_input
        self._global_scenario = global_scenario

        self._cluster_systems = {}
        self._cluster_env_inputs = {}
        self._cluster_ctrl_inputs = {}
        self._cluster_ctrl_limits = {}

        for global_node in self._global_scenario.network.nodes:
            system = ClusterSystem.from_real_system(self._real_system, self._global_scenario, global_node)
            self._cluster_systems[global_node.id] = [system for _ in range(self.control_sequence_length)]

            env_inputs = [ClusterEnvironmentInput.from_real_environment_input(real_env, self._global_scenario,
                                                                              global_node)
                          for real_env in self._real_environment_inputs]
            self._cluster_env_inputs[global_node.id] = env_inputs

            ctrl_limits = [ClusterControlLimit() for _ in range(self.control_sequence_length)]
            self._cluster_ctrl_limits[global_node.id] = ctrl_limits

            ctrl_inputs = [ClusterControlInput() for _ in range(self.control_sequence_length)]
            self._cluster_ctrl_inputs[global_node.id] = ctrl_inputs

        self._init_ext_info()

    def _init_ext_info(self):
        """Initialize information about external external nodes of each cluster
        """
        for node in self._global_scenario.network.nodes:
            system = self._cluster_systems[node.id][0]
            for time_step in range(self.control_sequence_length):
                ctrl_limit = self._cluster_ctrl_limits[node.id][time_step]
                env_input = self._cluster_env_inputs[node.id][time_step]

                for app in system.apps:
                    max_instances = app.max_instances
                    min_instances = 0
                    if self._global_control_input is not None:
                        max_instances = self._global_control_input.get_max_app_placement(app.id, node.id)
                        min_instances = self._global_control_input.get_min_app_placement(app.id, node.id)
                    ctrl_limit.max_app_placement[app.id] = max_instances
                    ctrl_limit.min_app_placement[app.id] = min_instances

                    for ext_node in self._global_scenario.network.nodes:
                        if node == ext_node:
                            continue

                        if self._global_control_input is not None:
                            # Estimate the number of instances in a external cluster
                            # as the max number of instances defined by the global controller
                            nb_instances = self._global_control_input.get_max_app_placement(app.id, ext_node.id)
                            env_input.nb_instances[app.id][ext_node.id] = nb_instances

                            max_dispatch_load = self._global_control_input.get_max_load(app.id, node.id, ext_node.id)
                            ctrl_limit.max_dispatch_load[app.id][ext_node.id] = max_dispatch_load

                            # Estimate the load from a external cluster as the max load allowed by the global controller
                            gen_load = self._global_control_input.get_max_load(app.id, ext_node.id, node.id)
                            if math.isinf(gen_load):
                                gen_load = 0.0
                            env_input.generated_load[app.id][ext_node.id] = gen_load
                        else:
                            env_input.nb_instances[app.id][ext_node.id] = 0
                            ctrl_limit.max_dispatch_load[app.id][ext_node.id] = math.inf
                            env_input.generated_load[app.id][ext_node.id] = 0.0

                        # Estimate arrive rate of an instance in a external cluster from other clusters as zero
                        env_input.additional_received_load[app.id][ext_node.id] = 0.0

    def _update_ext_info(self):
        """Update information of external nodes based on current control decisions
        """
        for node in self._global_scenario.network.nodes:
            for time_step in range(self.control_sequence_length):
                system = self._cluster_systems[node.id][time_step]
                ctrl_input = self._cluster_ctrl_inputs[node.id][time_step]
                ctrl_limit = self._cluster_ctrl_limits[node.id][time_step]
                env_input = self._cluster_env_inputs[node.id][time_step]

                for ext_node in self._global_scenario.network.nodes:
                    if node == ext_node:
                        continue

                    ext_system = self._cluster_systems[ext_node.id][time_step]
                    ext_ctrl_input = self._cluster_ctrl_inputs[ext_node.id][time_step]
                    ext_env_input = self._cluster_env_inputs[ext_node.id][time_step]
                    try:
                        cloud_node = ext_system.cloud_node
                    except AttributeError:
                        cloud_node = None

                    for app in ext_system.apps:
                        # Set number of instances of an external node
                        nb_instances = sum(map(lambda n: int(ext_ctrl_input.get_app_placement(app.id, n.id)),
                                               ext_system.internal_nodes))
                        env_input.nb_instances[app.id][ext_node.id] = nb_instances

                        # Set load from an external node
                        gen_load = sum(map(lambda n: calc_load_after_distribution(app.id, n.id, node.id,
                                                                                  ext_system, ext_ctrl_input,
                                                                                  ext_env_input, per_instance=False),
                                           ext_system.internal_nodes))
                        env_input.generated_load[app.id][ext_node.id] = gen_load

                        # Set load received by an instance in a external node that comes from other clusters
                        rec_load = sum(map(lambda n: calc_received_load(app.id, n.id, ext_system,
                                                                        ext_ctrl_input, ext_env_input),
                                           ext_system.internal_nodes))
                        # print(node.id, ext_node.id, app.id, nb_instances, rec_load)
                        rec_load -= sum(map(lambda n: calc_load_after_distribution(app.id, node.id, n.id,
                                                                                   ext_system, ext_ctrl_input,
                                                                                   ext_env_input, per_instance=False),
                                            ext_system.internal_nodes))
                        # print(node.id, ext_node.id, app.id, nb_instances, rec_load)
                        rec_load = rec_load / float(nb_instances) if nb_instances > 0 and rec_load > 0.0 else 0.0
                        env_input.additional_received_load[app.id][ext_node.id] = rec_load
                        # print("update ext", node.id, ext_node.id, app.id, nb_instances, rec_load)

                        # Set max dispatch load to an external node
                        if ext_node.is_cloud():
                            ctrl_limit.max_dispatch_load[app.id][ext_node.id] = math.inf
                        else:
                            cloud_load = 0.0
                            if cloud_node is not None:
                                cloud_load = calc_load_after_distribution(app.id, node.id, cloud_node.id,
                                                                          ext_system, ext_ctrl_input, ext_env_input,
                                                                          per_instance=False)
                            max_load = ctrl_limit.max_dispatch_load[app.id][ext_node.id]
                            if cloud_load > 0.0:
                                max_load = max(0.0, max_load - cloud_load)

                            ext_load = sum(map(lambda n: calc_load_after_distribution(app.id, n.id, ext_node.id,
                                                                                      system, ctrl_input, env_input,
                                                                                      per_instance=False),
                                               system.internal_nodes))
                            ctrl_limit.max_dispatch_load[app.id][ext_node.id] = min(max_load, ext_load)
