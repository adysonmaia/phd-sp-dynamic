from sp.core.model import Scenario
from sp.core.predictor import AutoARIMAPredictor, SARIMAPredictor, NaivePredictor
from sp.simulator import Simulator
from sp.simulator.monitor import OptimizerMonitor, EnvironmentMonitor
from sp.system_controller import metric, util
from sp.system_controller.optimizer.llc import LLCOptimizer, plan_finder, input_finder
from sp.system_controller.optimizer import SOGAOptimizer, MOGAOptimizer, CloudOptimizer, SOHeuristicOptimizer
from sp.system_controller.optimizer import OmittedMigrationOptimizer, StaticOptimizer
from sp.system_controller.predictor import MultiProcessingEnvironmentPredictor
from datetime import datetime
from pytz import timezone
import json
import math
import os
import time
# import logging
# logging.basicConfig(level=logging.DEBUG)


UTC_TZ = timezone('UTC')
SF_TZ_STR = 'US/Pacific'
SF_TZ = timezone(SF_TZ_STR)


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

        tz_time = datetime.fromtimestamp(sim_time, tz=UTC_TZ).astimezone(SF_TZ)
        print_prefix = '{}: '.format(self.debug_prefix) if self.debug_prefix else ''
        print('{}{}/{} - {} - {:9.3f}s'.format(print_prefix, time_slot, total_time_slot, tz_time, elapsed_time))

        print('Metrics')
        metrics_id = list(datum.keys())
        metrics_id.sort()
        for metric_id in metrics_id:
            print('{:40}: {}'.format(metric_id, datum[metric_id]))

        # print('\nApplications')
        # for app in system.apps:
        #     places = [n.id for n in system.nodes if control_input.get_app_placement(app.id, n.id)]
        #     users = environment_input.get_attached_users()
        #     users = list(filter(lambda u: u.app_id == app.id and u.node_id is not None, users))
        #     load = sum([util.calc_load_before_distribution(app.id, node.id, system, environment_input)
        #                 for node in system.nodes])
        #     overall_violation = util.filter_metric(metric.deadline.overall_deadline_violation,
        #                                            system, control_input, environment_input,
        #                                            apps_id=app.id)
        #     max_violation = util.filter_metric(metric.deadline.max_deadline_violation,
        #                                        system, control_input, environment_input,
        #                                        apps_id=app.id)
        #     print('app {:2d} {:>5}, deadline {:6.1f}ms, max instances {:2d}, users {:4d}, load {:10.3f}, '
        #           'max violation {:9.6f}s, overall violation {:9.6f}s, '
        #           'places {:2d}: {}'.format(
        #         app.id, app.type, 1000 * app.deadline, app.max_instances, len(users), load,
        #         overall_violation, max_violation, len(places), places
        #     ))
        #
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


def main():
    """Main function
    """
    # Load simulation parameters
    root_output_path = 'output/san_francisco/exp/'
    simulation_filename = 'input/san_francisco/simulation.json'
    simulation_data = None
    with open(simulation_filename) as json_file:
        simulation_data = json.load(json_file)
    simulation_time = simulation_data['time']

    # Set objectives and metrics functions
    optimizers = []
    multi_objective = [
        metric.deadline.weighted_avg_deadline_violation,
        metric.response_time.weighted_avg_response_time,
        metric.cost.overall_cost,
        metric.migration.weighted_migration_rate,
    ]
    multi_objective_without_migration = [
        metric.deadline.weighted_avg_deadline_violation,
        metric.response_time.weighted_avg_response_time,
        metric.cost.overall_cost,
    ]
    single_objective = metric.response_time.weighted_avg_response_time
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
    # pool_size = 12
    # pool_size = 8
    pool_size = 4
    # pool_size = 0
    # timeout = 3 * 60  # 3 min
    # timeout = 2 * 60  # 2 min
    timeout = 1 * 60  # 1 min
    ga_pop_size = 100
    # ga_pop_size = 50
    # ga_nb_gens = 100
    ga_nb_gens = 50

    # Set environment forecasting
    env_predictor = MultiProcessingEnvironmentPredictor()
    env_predictor.pool_size = pool_size
    env_predictor.load_predictor_class = SARIMAPredictor
    env_predictor.load_predictor_params = {'order': (1, 1, 0), 'enforce_stationarity': False,
                                           'enforce_invertibility': False}
    # env_predictor.load_predictor_class = AutoARIMAPredictor
    # # env_predictor.load_predictor_params = {'max_p': 3, 'max_q': 3, 'stepwise': True, 'maxiter': 10}
    # env_predictor.load_predictor_params = {'max_p': 3, 'max_q': 3, 'stepwise': False,
    #                                        'random': True, 'n_fits': 2, 'maxiter': 2}
    env_predictor.net_delay_predictor_class = NaivePredictor

    # Set optimizer solutions

    # Cloud optimizer config
    opt = CloudOptimizer()
    opt_id = opt.__class__.__name__
    item = (opt_id, opt)
    optimizers.append(item)

    # Single-Objective Heuristic optimizer config
    opt = SOHeuristicOptimizer()
    opt_id = opt.__class__.__name__
    item = (opt_id, opt)
    optimizers.append(item)

    # Single-Objective GA optimizer config
    opt = SOGAOptimizer()
    opt.objective = single_objective
    opt.timeout = timeout
    opt.population_size = ga_pop_size
    opt.nb_generations = ga_nb_gens
    opt_id = opt.__class__.__name__
    item = (opt_id, opt)
    # optimizers.append(item)

    # Static Optimizer
    opt = StaticOptimizer()
    opt.objective = multi_objective
    opt.pool_size = pool_size
    opt.timeout = timeout
    opt.population_size = ga_pop_size
    opt.nb_generations = ga_nb_gens
    opt.dominance_func = dominance_func
    opt_id = opt.__class__.__name__
    item = (opt_id, opt)
    optimizers.append(item)

    # Omitted Migration optimizer config
    opt = OmittedMigrationOptimizer()
    opt.objective = multi_objective_without_migration
    opt.pool_size = pool_size
    opt.timeout = timeout
    opt.population_size = ga_pop_size
    opt.nb_generations = ga_nb_gens
    opt.dominance_func = dominance_func
    opt_id = opt.__class__.__name__
    item = (opt_id, opt)
    # optimizers.append(item)

    # Multi-Objective GA optimizer config
    opt = MOGAOptimizer()
    opt.objective = multi_objective
    opt.pool_size = pool_size
    opt.timeout = timeout
    opt.population_size = ga_pop_size
    opt.nb_generations = ga_nb_gens
    opt.dominance_func = dominance_func
    opt_id = opt.__class__.__name__
    item = (opt_id, opt)
    optimizers.append(item)

    # LLC Parameters

    # LLC (control input and plan) finders versions
    llc_finders = [
        {
            'id': 'ssga',
            'input': input_finder.SSGAInputFinder,
            'input_params': {'timeout': timeout, 'population_size': ga_pop_size, 'nb_generations': ga_nb_gens},
            'plan': None
        },
        {
            'id': 'sga',
            'input': input_finder.SGAInputFinder,
            'input_params': {'timeout': timeout, 'population_size': ga_pop_size, 'nb_generations': ga_nb_gens},
            'plan': None
        },
        # {
        #     'id': 'mga',
        #     'input': input_finder.MGAInputFinder,
        #     'input_params': {'timeout': timeout},
        #     'plan': plan_finder.GAPlanFinder,
        #     'plan_params': {'timeout': timeout},
        # },
        # {
        #     'id': 'ssga_sga',
        #     'input': input_finder.PipelineInputFinder,
        #     'plan': None
        # },
    ]

    # Prediction windows
    # prediction_windows = [0, 1, 2]
    # prediction_windows = [1, 2]
    # prediction_windows = [0]
    prediction_windows = [1]
    # prediction_windows = [2]

    for window in prediction_windows:
        for llc_finder in llc_finders:
            opt = LLCOptimizer()
            opt.prediction_window = window
            opt.pool_size = pool_size
            opt.dominance_func = dominance_func
            opt.objective = multi_objective
            opt.objective_aggregator = util.sum_aggregator
            opt.input_finder_class = llc_finder['input']
            opt.input_finder_params = llc_finder['input_params'] if 'input_params' in llc_finder else None
            opt.plan_finder_class = llc_finder['plan']
            opt.plan_finder_params = llc_finder['plan_params'] if 'plan_params' in llc_finder else None
            opt.environment_predictor = env_predictor

            opt_id = '{}_{}_w{}'.format(opt.__class__.__name__, llc_finder['id'], window)
            item = (opt_id, opt)
            optimizers.append(item)

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
        elapsed_time = time.perf_counter() - perf_count
        print('finished in {:5.2f}s'.format(elapsed_time))

        # Obtain forecasting training set
        if 'train_start' in time_data and time_data['train_start'] < time_data['start']:
            time_start, time_stop, time_step = time_data['train_start'], time_data['start'] - 1, time_data['step']
            env_log_path = os.path.join(root_output_path, scenario_id, str(run))
            load_log_filename = os.path.join(env_log_path, 'load.json')

            seasonal_period = int(round(1 * 24 * 60 * 60 / float(time_step)))  # Seasonal of 1 day
            seasonal_params = {'seasonal_order': (1, 0, 0, seasonal_period)}
            # seasonal_params = {'seasonal': True, 'm': seasonal_period}
            # env_predictor.load_predictor_params.update(seasonal_params)
            env_predictor.load_predictor_params.update(seasonal_params)
            env_predictor.load_init_data = load_log_filename

            if not os.path.exists(load_log_filename) or not os.path.isfile(load_log_filename):
                print('generating training set ...', end=' ')
                perf_count = time.perf_counter()
                sim = Simulator(scenario=scenario)
                sim.set_time(start=time_start, stop=time_stop, step=time_step)
                sim.optimizer = CloudOptimizer()
                sim.monitor = EnvironmentMonitor(output_path=env_log_path, log_load=True, log_net_delay=False)
                sim.run()
                elapsed_time = time.perf_counter() - perf_count
                print('finished in {:6.2f}s'.format(elapsed_time))

        # Execute simulation for each optimizer nb_runs times
        for (opt_id, opt) in optimizers:
            # Set simulation output parameters
            output_sub_path = '{}/{}/{}'.format(scenario_id, run, opt_id)
            output_path = os.path.join(root_output_path, output_sub_path)
            debug_prefix = output_sub_path
            try:
                os.makedirs(output_path)
            except OSError:
                pass

            # Set simulation parameters
            time_start, time_stop, time_step = time_data['start'], time_data['stop'], time_data['step']
            sim = Simulator(scenario=scenario)
            sim.set_time(start=time_start, stop=time_stop, step=time_step)
            sim.optimizer = opt
            sim.monitor = ExpRunMonitor(metrics_func=metrics, output_path=output_path, debug_prefix=debug_prefix)
            # sim.monitor = ExpRunMonitor(metrics_func=metrics, output_path=None, debug_prefix=debug_prefix)

            # Run simulation
            perf_count = time.perf_counter()
            sim.run()
            elapsed_time = time.perf_counter() - perf_count
            print('scenario {}, run {}, opt {} - sim exec time: {}s'.format(scenario_id, run, opt_id, elapsed_time))


if __name__ == '__main__':
    main()
