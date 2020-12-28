from sp.core.model import Scenario
from sp.core.predictor import AutoARIMAPredictor, SARIMAPredictor, NaivePredictor
from sp.core.util import json_util
from sp.simulator import Simulator
from sp.simulator.monitor import OptimizerMonitor, EnvironmentMonitor
from sp.system_controller import metric, util
from sp.system_controller.predictor import MultiProcessingEnvironmentPredictor
from sp.hierarchical_controller.system_controller import HierarchicalSystemController
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario
from sp.hierarchical_controller.global_ctrl.scheduler import GlobalPeriodicScheduler
from sp.hierarchical_controller.global_ctrl.optimizer import GlobalMOGAOptimizer, GlobalLLGAOptimizer
from sp.hierarchical_controller.global_ctrl.optimizer.llga import SimpleGlobalLLGAOperator, GeneralGlobalLLGAOperator
from sp.hierarchical_controller.global_ctrl.predictor import GlobalEnvironmentPredictor
from sp.hierarchical_controller.global_ctrl import metric as global_metric
from sp.hierarchical_controller.cluster_ctrl.optimizer import ClusterLLGAOptimizer
from sp.hierarchical_controller.cluster_ctrl.optimizer.llga import SimpleClusterLLGAOperator, GeneralClusterLLGAOperator
from sp.hierarchical_controller.cluster_ctrl import metric as cluster_metric
from collections import defaultdict
import json
import math
import os
import time
import gc
# import logging
# logging.basicConfig(level=logging.DEBUG)


class ExpRunMonitor(OptimizerMonitor):
    """Simulation monitor
    """

    def __init__(self, metrics_func, output_path=None, debug_prefix=None):
        """Initialization

        Args:
             metrics_func (list): list of metric functions
             output_path (str): path to save the logs
             debug_prefix (str): debug print prefix
        """
        OptimizerMonitor.__init__(self, metrics_func, output_path)
        self.debug_prefix = debug_prefix
        self.valid_checking_extra_params = {'allow_surplus_alloc': True}

        self._times_data = []
        self._cluster_perf_count = defaultdict(lambda: 0.0)
        self._global_perf_count = 0
        self._all_clusters_perf_count = 0

    def on_global_ctrl_started(self, sim_time):
        """Event dispatched when the global controller update started

        Args:
            sim_time (float): current simulation time
        """
        self._global_perf_count = time.perf_counter()

    def on_global_ctrl_ended(self, sim_time, **kwargs):
        """Event dispatched when the global controller update ended

        Args:
            sim_time (float): current simulation time
            **kwargs:
        """
        elapsed_time = time.perf_counter() - self._global_perf_count
        datum = {'time': sim_time, 'elapsed_time': elapsed_time, 'id': -1, 'type': 'global'}
        self._times_data.append(datum)
        print(datum)

    def on_all_cluster_ctrls_started(self, sim_time):
        """Event dispatched when the update of all cluster controllers started

        Args:
            sim_time (float): current simulation time
        """
        self._all_clusters_perf_count = time.perf_counter()

    def on_all_cluster_ctrls_ended(self, sim_time, **kwargs):
        """Event dispatched when the update of all cluster controllers ended

        Args:
            sim_time (float): current simulation time
            **kwargs:
        """
        elapsed_time = time.perf_counter() - self._all_clusters_perf_count
        datum = {'time': sim_time, 'elapsed_time': elapsed_time, 'id': -2, 'type': 'all_clusters'}
        self._times_data.append(datum)
        print(datum)

    def on_cluster_ctrl_started(self, sim_time, cluster_id):
        """Event dispatched when a cluster controller update started

        Args:
            sim_time (float): current simulation time
            cluster_id (int): cluster's id
        """
        self._cluster_perf_count[cluster_id] = time.perf_counter()

    def on_cluster_ctrl_ended(self, sim_time, cluster_id, **kwargs):
        """Event dispatched when a cluster controller update ended

        Args:
            sim_time (float): current simulation time
            cluster_id (int): cluster's id
            **kwargs:
        """
        elapsed_time = time.perf_counter() - self._cluster_perf_count[cluster_id]
        datum = {'time': sim_time, 'elapsed_time': elapsed_time, 'id': cluster_id, 'type': 'cluster'}
        self._times_data.append(datum)
        print(datum)

    def on_sys_ctrl_ended(self, sim_time, system, control_input, environment_input):
        """Event dispatched when the system controller update ended

        Args:
            sim_time (float): current simulation time
            system (sp.core.model.System): current system state
            control_input (sp.core.model.ControlInput): new control input after the controller update
            environment_input (sp.core.model.EnvironmentInput): current environment input
        """
        OptimizerMonitor.on_sys_ctrl_ended(self, sim_time, system, control_input, environment_input)

        datum = self._metrics_data[-1]
        elapsed_time = datum['elapsed_time']

        time_slot = (sim_time - self.simulator.start_time) / float(self.simulator.step_time)
        time_slot = int(math.floor(time_slot)) + 1
        total_time_slot = (self.simulator.stop_time - self.simulator.start_time) / float(self.simulator.step_time)
        total_time_slot = int(math.floor(total_time_slot)) + 1

        print_prefix = '{}: '.format(self.debug_prefix) if self.debug_prefix else ''
        print('{}{}/{} - {:9.3f}s'.format(print_prefix, time_slot, total_time_slot, elapsed_time))

        print('Metrics')
        metrics_id = list(datum.keys())
        metrics_id.sort()
        for metric_id in metrics_id:
            print('{:40}: {}'.format(metric_id, datum[metric_id]))

        print('\nApplications')
        for app in system.apps:
            places = [n.id for n in system.nodes if control_input.get_app_placement(app.id, n.id)]
            users = environment_input.get_attached_users()
            users = list(filter(lambda u: u.app_id == app.id and u.node_id is not None, users))
            load = sum([util.calc_load_before_distribution(app.id, node.id, system, environment_input)
                        for node in system.nodes])
            overall_violation = util.filter_metric(metric.deadline.overall_deadline_violation,
                                                   system, control_input, environment_input,
                                                   apps_id=app.id)
            max_violation = util.filter_metric(metric.deadline.max_deadline_violation,
                                               system, control_input, environment_input,
                                               apps_id=app.id)
            print('app {:2d} {:>5}, deadline {:6.1f}ms, max instances {:2d}, users {:4d}, load {:10.3f}, '
                  'max violation {:9.6f}s, overall violation {:9.6f}s, '
                  'places {:2d}: {}'.format(
                app.id, app.type, 1000 * app.deadline, app.max_instances, len(users), load,
                overall_violation, max_violation, len(places), places
            ))

        # print('\nFree Resources')
        # for node in system.nodes:
        #     free_str = 'node {:2d}, '.format(node.id)
        #     for resource in system.resources:
        #         capacity = node.capacity[resource.name]
        #         alloc = sum([control_input.get_allocated_resource(a.id, node.id, resource.name) for a in system.apps])
        #         free = 1.0
        #         if capacity > 0.0 and not math.isinf(capacity):
        #             free = (capacity - alloc) / float(capacity)
        #             free = round(free, 3)
        #         free_str += '{} {:6.3f}, '.format(resource.name, free)
        #     print(free_str)

        # print('\nLoad Distribution')
        # for app in system.apps:
        #     for src_node in system.nodes:
        #         ld = ['{:4.2f}'.format(control_input.get_load_distribution(app.id, src_node.id, dst_node.id))
        #               for dst_node in system.nodes]
        #         print('app {:2d}, node {:2d}, ld: {}'.format(app.id, src_node.id, ld))

        print("--")

    def on_sim_ended(self, sim_time):
        """Event dispatched when the simulation ended

        Args:
            sim_time (float): current simulation time
        """
        OptimizerMonitor.on_sim_ended(self, sim_time)
        if self.output_path is None:
            return

        times_filename = os.path.join(self.output_path, 'times.json')
        with open(times_filename, 'w') as file:
            json.dump(self._times_data, file, indent=2)


def main():
    """Main function
    """
    # Load simulation parameters
    root_output_path = 'output/hierarchical/exp/'
    simulation_filename = 'input/hierarchical/simulation.json'
    simulation_data = None
    with open(simulation_filename) as json_file:
        simulation_data = json.load(json_file)
    simulation_time = simulation_data['time']

    # Set global parameters
    global_optimizers = []
    global_multi_objective = [
        global_metric.deadline.weighted_avg_deadline_violation,
        global_metric.cost.overall_cost,
        global_metric.response_time.weighted_avg_response_time,
    ]
    global_period = 2

    # Set cluster parameters
    cluster_multi_objective = [
        cluster_metric.deadline.weighted_avg_deadline_violation,
        cluster_metric.cost.overall_cost,
        cluster_metric.migration.weighted_migration_rate,
    ]
    cluster_optimizers = []

    # Set metric functions
    metrics = [
        metric.deadline.overall_deadline_violation,
        metric.deadline.weighted_overall_deadline_violation,
        metric.deadline.max_deadline_violation,
        metric.deadline.avg_deadline_violation,
        metric.deadline.avg_only_violated_deadline,
        metric.deadline.weighted_avg_deadline_violation,
        metric.deadline.weighted_avg_only_violated_deadline,
        metric.deadline.deadline_satisfaction,
        metric.deadline.weighted_deadline_satisfaction,
        metric.cost.overall_cost,
        metric.cost.max_cost,
        metric.cost.avg_cost,
        metric.migration.overall_migration_cost,
        metric.migration.max_migration_cost,
        metric.migration.avg_migration_cost,
        metric.migration.migration_rate,
        metric.migration.weighted_migration_rate,
        metric.response_time.overall_response_time,
        metric.response_time.weighted_overall_response_time,
        metric.response_time.max_response_time,
        metric.response_time.avg_response_time,
        metric.response_time.weighted_avg_response_time,
        metric.availability.avg_unavailability,
        metric.power.overall_power_consumption,
    ]

    #
    dominance_func = util.preferred_dominates
    # pool_size = 16
    # pool_size = 12
    pool_size = 8
    # pool_size = 4
    # pool_size = 0
    # timeout = 3 * 60  # 3 min
    # timeout = 2 * 60  # 2 min
    timeout = 1 * 60  # 1 min
    # timeout = None
    ga_pop_size = 100
    # ga_pop_size = 50
    # ga_nb_gens = 100
    ga_nb_gens = 50

    # GA parameters as dict
    ga_params = {
        'nb_generations': ga_nb_gens,
        'population_size': ga_pop_size,
        'timeout': timeout,
        'pool_size': pool_size,
        'dominance_func': dominance_func,
    }
    ga_operator_params = {}

    # Set environment forecasting
    env_predictor = MultiProcessingEnvironmentPredictor()
    env_predictor.pool_size = pool_size
    env_predictor.load_predictor_class = AutoARIMAPredictor
    env_predictor.load_predictor_params = {'max_p': 3, 'max_q': 3, 'stepwise': True, 'maxiter': 10}
    # env_predictor.load_predictor_params = {'max_p': 3, 'max_q': 3, 'stepwise': False,
    #                                        'random': True, 'n_fits': 2, 'maxiter': 2}
    env_predictor.net_delay_predictor_class = NaivePredictor

    # Set global environment forecasting
    global_env_predictor = GlobalEnvironmentPredictor()
    global_env_predictor.real_environment_predictor = env_predictor

    # Set optimizer solutions

    # Global Multi-Objective GA optimizer config
    opt = GlobalMOGAOptimizer()
    opt.objective = global_multi_objective
    opt.pool_size = pool_size
    opt.timeout = timeout
    opt.population_size = ga_pop_size
    opt.nb_generations = ga_nb_gens
    opt.dominance_func = dominance_func
    opt.environment_predictor = global_env_predictor
    opt_id = opt.__class__.__name__
    item = (opt_id, opt)
    global_optimizers.append(item)

    # Global LLC Optimizer
    # global_prediction_windows = [1]
    # # global_llga_operators = [SimpleGlobalLLGAOperator, GeneralGlobalLLGAOperator]
    # global_llga_operators = [GeneralGlobalLLGAOperator]
    #
    # for window in global_prediction_windows:
    #     for ga_operator in global_llga_operators:
    #         opt = GlobalLLGAOptimizer()
    #         opt.prediction_window = window
    #         opt.ga_params = ga_params
    #         opt.ga_operator_class = ga_operator
    #         opt.ga_operator_params = ga_operator_params
    #         opt.objective = global_multi_objective
    #         opt.environment_predictor = global_env_predictor
    #
    #         opt_id = '{}_w{}'.format(ga_operator.__name__, window)
    #         item = (opt_id, opt)
    #         # global_optimizers.append(item)

    # CLuster LLC Optimizer
    cluster_pool_size = 0
    cluster_prediction_windows = [1]
    # cluster_max_iterations = [0, 1, 2]
    cluster_max_iterations = [1]
    # cluster_llga_operators = [SimpleClusterLLGAOperator, GeneralClusterLLGAOperator]
    cluster_llga_operators = [GeneralClusterLLGAOperator]

    for max_iteration in cluster_max_iterations:
        for window in cluster_prediction_windows:
            for ga_operator in cluster_llga_operators:
                opt = ClusterLLGAOptimizer()
                opt.objective = cluster_multi_objective
                opt.prediction_window = window
                opt.ga_params = ga_params
                opt.ga_operator_class = ga_operator
                opt.ga_operator_params = ga_operator_params
                opt.max_iteration = max_iteration
                opt.pool_size = cluster_pool_size

                opt_id = '{}_w{}_i{}'.format(ga_operator.__name__, window, max_iteration)
                item = (opt_id, opt)
                cluster_optimizers.append(item)

    clusters = None
    if 'clusters' in simulation_data:
        clusters = json_util.load_key_content(simulation_data, 'clusters')

    # Create a simulation for each loaded scenario
    for scenario_data in simulation_data['scenarios']:
        scenario_filename = scenario_data['scenario']
        scenario_id = scenario_data['scenario_id']
        run = scenario_data['run']
        time_data = simulation_time
        if 'time' in scenario_data:
            time_data.update(scenario_data['time'])

        print('loading scenario {} ...'.format(scenario_filename), end=' ')
        perf_count = time.perf_counter()
        scenario = None
        with open(scenario_filename) as json_file:
            scenario_json = json.load(json_file)
            scenario = Scenario.from_json(scenario_json)
            if 'clusters' in scenario_json:
                clusters = json_util.load_key_content(scenario_json, 'clusters')
        elapsed_time = time.perf_counter() - perf_count
        print('finished in {:5.2f}s'.format(elapsed_time))

        # Create scenario for global controller
        if clusters is None:
            clusters = [[n.id] for n in scenario.network.nodes]
        global_scenario = GlobalScenario.from_real_scenario(scenario, clusters)

        # Execute simulation for each optimizer nb_runs times
        for (global_opt_id, global_opt) in global_optimizers:
            for (cluster_opt_id, cluster_opt) in cluster_optimizers:
                # Set simulation output parameters
                output_sub_path = '{}/{}/{}_{}'.format(scenario_id, run, global_opt_id, cluster_opt_id)
                output_path = os.path.join(root_output_path, output_sub_path)
                debug_prefix = output_sub_path
                try:
                    os.makedirs(output_path)
                except OSError:
                    pass

                metrics_filename = os.path.join(output_path, 'metrics.json')
                if os.path.isfile(metrics_filename):
                    continue

                # Set simulation parameters
                time_start, time_stop, time_step = time_data['start'], time_data['stop'], time_data['step']
                sim = Simulator(scenario=scenario)
                sim.set_time(start=time_start, stop=time_stop, step=time_step)

                global_scheduler = GlobalPeriodicScheduler()
                global_scheduler.period = global_period
                global_scheduler.global_scenario = global_scenario
                global_scheduler.environment_predictor = global_env_predictor

                monitor = ExpRunMonitor(metrics_func=metrics, output_path=output_path, debug_prefix=debug_prefix)
                cluster_opt.monitor = monitor

                controller = HierarchicalSystemController()
                controller.global_scenario = global_scenario
                controller.global_optimizer = global_opt
                controller.global_scheduler = global_scheduler
                controller.optimizer = cluster_opt
                controller.monitor = monitor

                sim.system_controller = controller
                sim.monitor = monitor

                # Run simulation
                perf_count = time.perf_counter()
                sim.run()
                elapsed_time = time.perf_counter() - perf_count
                print('scenario {}, run {}, opt ({}, {}) - sim exec time: {}s'.format(scenario_id, run, global_opt_id,
                                                                                      opt_id, elapsed_time))

            scenario = None
            global_scenario = None
            gc.collect()


if __name__ == '__main__':
    main()
