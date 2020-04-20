from sp.core.model import Scenario
from sp.core.predictor import AutoARIMAPredictor
from sp.simulator import Simulator, Monitor
from sp.system_controller.optimizer.llc import LLCOptimizer
from sp.system_controller.optimizer.llc import plan_finder
from sp.system_controller.optimizer import SOGAOptimizer, MOGAOptimizer, CloudOptimizer, SOHeuristicOptimizer
from sp.system_controller.predictor import DefaultEnvironmentPredictor
from sp.system_controller import metric, utils
from datetime import datetime
from pytz import timezone
import json
import time
import os
import logging
logging.basicConfig(level=logging.DEBUG)


UTC_TZ = timezone('UTC')
SF_TZ_STR = 'US/Pacific'
SF_TZ = timezone(SF_TZ_STR)


def get_app_deadline_violation(app, system, control_input, environment_input):
    violation = 0.0
    for dst_node in system.nodes:
        if not control_input.get_app_placement(app.id, dst_node.id):
            continue

        src_nodes = [n.id for n in system.nodes if control_input.get_load_distribution(app.id, n.id, dst_node.id) > 0]
        alloc = control_input.get_allocated_cpu(app.id, dst_node.id)
        load = utils.calc_load_before_distribution(app.id, dst_node.id, system, environment_input)
        ld = control_input.get_load_distribution(app.id, dst_node.id, dst_node.id)
        # print('app {}, dst {}, src {}'.format(app.id, dst_node.id, src_nodes))
        # print('\tcpu {}, alloc {}, ld {}, load {}'.format(dst_node.cpu_capacity, alloc, ld, load))

        for src_node in system.nodes:
            load = utils.calc_load_after_distribution(app.id, src_node.id, dst_node.id,
                                                      system, control_input, environment_input)
            if load > 0.0:
                rt = utils.calc_response_time(app.id, src_node.id, dst_node.id,
                                              system, control_input, environment_input)
                if rt > app.deadline:
                    # ld = control_input.get_load_distribution(app.id, src_node.id, dst_node.id)
                    # net_delay = environment_input.get_net_delay(app.id, src_node.id, dst_node.id)
                    # proc_delay = calc_processing_delay(app.id, dst_node.id, system, control_input, environment_input)
                    # init_delay = calc_initialization_delay(app.id, dst_node.id, system, control_input, environment_input)
                    # print(app.id, src_node.id, dst_node.id, ld, rt, app.deadline, net_delay, proc_delay, init_delay)
                    violation += rt - app.deadline
    return violation


class ControlMonitor(Monitor):
    """Simulation monitor
    """
    def __init__(self, metrics_func, output_path=None):
        """Initialization
        Args:
             metrics_func (list): list of metric functions
             output_path (str): path to save the logs
        """
        Monitor.__init__(self)
        self.metrics_func = metrics_func  # metric functions
        self.metrics_data = list()  # log of metric data
        self.control_data = dict()  # log of control data
        self.perf_count = 0  # last performance count
        self.output_path = output_path

    def on_sim_started(self, sim_time):
        """Event dispatched when the simulation started
        Args:
            sim_time (float): current simulation time
        """
        self.metrics_data.clear()
        self.control_data = {'place': [], 'alloc': [], 'ld': []}
        self.perf_count = 0

    def on_sys_ctrl_started(self, sim_time, system, environment_input):
        """Event dispatched when the system controller update started
        Args:
            sim_time (float): current simulation time
            system (sp.core.model.System): current system state
            environment_input (sp.core.model.EnvironmentInput): current environment input
        """
        self.perf_count = time.perf_counter()

    def on_sys_ctrl_ended(self, sim_time, system, control_input, environment_input):
        """Event dispatched when the system controller update ended
        Args:
            sim_time (float): current simulation time
            system (sp.core.model.System): current system state
            control_input (sp.core.model.ControlInput): new control input after the controller update
            environment_input (sp.core.model.EnvironmentInput): current environment input
        """
        opt_name = self.simulator.optimizer.__class__.__name__
        elapsed_time = time.perf_counter() - self.perf_count

        tz_time = datetime.fromtimestamp(sim_time, tz=UTC_TZ).astimezone(SF_TZ)
        print('{} - {}s'.format(tz_time, elapsed_time))

        valid = utils.is_solution_valid(system, control_input, environment_input)
        datum = {'time': sim_time, 'opt': opt_name, 'elapsed_time': elapsed_time, 'valid': valid}
        for func in self.metrics_func:
            key = func.__name__
            value = func(system, control_input, environment_input)
            datum[key] = value
        self.metrics_data.append(datum)
        print(datum)

        place_datum = []
        alloc_datum = []
        ld_datum = []
        for app in system.apps:
            for dst_node in system.nodes:
                value = control_input.get_app_placement(app.id, dst_node.id)
                item = {'time': sim_time, 'app': app.id, 'node': dst_node.id, 'place': value}
                place_datum.append(item)

                item = {'time': sim_time, 'app': app.id, 'node': dst_node.id}
                for resource in system.resources:
                    value = control_input.get_allocated_resource(app.id, dst_node.id, resource.name)
                    item[resource.name] = value
                alloc_datum.append(item)

                for src_node in system.nodes:
                    load = utils.calc_load_before_distribution(app.id, src_node.id, system, environment_input)
                    ld = control_input.get_load_distribution(app.id, src_node.id, dst_node.id)
                    item = {'time': sim_time, 'app': app.id,
                            'src_node': src_node.id, 'dst_node': dst_node.id, 'ld': ld, 'load': load}
                    ld_datum.append(item)

        self.control_data['place'] += place_datum
        self.control_data['ld'] += ld_datum
        self.control_data['alloc'] += alloc_datum

        for app in system.apps:
            places = [n.id for n in system.nodes if control_input.get_app_placement(app.id, n.id)]
            users = environment_input.get_attached_users()
            users = list(filter(lambda u: u.app_id == app.id and u.node_id is not None, users))
            deadline_violation = get_app_deadline_violation(app, system, control_input, environment_input)
            print('app {} {}, deadline {}ms, users {}, places {}: {}, deadline violation {}ms'.format(
                app.id, app.type, 1000 * app.deadline, len(users), len(places), places, deadline_violation
            ))

            # for src_node in system.nodes:
            #     load = utils.calc_load_before_distribution(app.id, src_node.id, system, environment_input)
            #     dst_nodes = [n.id for n in system.nodes
            #                  if control_input.get_load_distribution(app.id, src_node.id, n.id) > 0]
            #     print('\t from {} to {}, load {}'.format(src_node.id, dst_nodes, load))

        print("--")

    def on_sim_ended(self, sim_time):
        if self.output_path is None:
            return

        metrics_filename = os.path.join(self.output_path, 'metrics.json')
        place_filename = os.path.join(self.output_path, 'placement.json')
        alloc_filename = os.path.join(self.output_path, 'allocation.json')
        ld_filename = os.path.join(self.output_path, 'load_distribution.json')

        files_data = [
            (metrics_filename, self.metrics_data),
            (place_filename, self.control_data['place']),
            (alloc_filename, self.control_data['alloc']),
            (ld_filename, self.control_data['ld']),
        ]

        # for (filename, data) in files_data:
        #     with open(filename, 'w') as file:
        #         json.dump(data, file, indent=2)


def main():
    """Main function
    """

    # Read input
    scenario_filename = 'input/san_francisco/scenario.json'
    scenario = None
    with open(scenario_filename) as json_file:
        data = json.load(json_file)
        scenario = Scenario.from_json(data)

    # Set simulation time
    start_time = SF_TZ.localize(datetime(2008, 5, 24, 0, 0, 0)).timestamp()
    stop_time = SF_TZ.localize(datetime(2008, 5, 24, 23, 59, 59)).timestamp()
    # stop_time = SF_TZ.localize(datetime(2008, 5, 25, 23, 59, 59)).timestamp()
    # step_time = 10 * 60  # seconds or 10 min
    step_time = 60 * 60  # seconds or 1H
    # step_time = 30 * 60  # seconds or 30 min

    # Set optimizer solutions
    optimizers = []
    metrics = [
        metric.deadline.overall_deadline_violation,
        metric.cost.overall_cost,
        metric.migration.overall_migration_cost,

        metric.deadline.max_deadline_violation,
        metric.deadline.avg_deadline_violation,
        metric.deadline.deadline_satisfaction,
        metric.migration.overall_migration_cost,
        metric.availability.avg_unavailability,
        metric.response_time.overall_response_time,
        metric.response_time.avg_response_time,
        metric.response_time.max_response_time,
        metric.power.overall_power_consumption,
    ]
    multi_objective = [
        metric.deadline.overall_deadline_violation,
        metric.cost.overall_cost,
        metric.migration.overall_migration_cost,
    ]
    single_objective = multi_objective[0]

    # dominance_func = utils.pareto_dominates
    dominance_func = utils.preferred_dominates
    pool_size = 8

    # Cloud optimizer config
    opt = CloudOptimizer()
    opt_id = opt.__class__.__name__
    item = (opt_id, opt)
    # optimizers.append(item)

    # Single-Objective Heuristic optimizer config
    opt = SOHeuristicOptimizer()
    opt_id = opt.__class__.__name__
    item = (opt_id, opt)
    # optimizers.append(item)

    # Single-Objective GA optimizer config
    opt = SOGAOptimizer()
    opt.objective = single_objective
    opt_id = opt.__class__.__name__
    item = (opt_id, opt)
    # optimizers.append(item)

    # Multi-Objective GA optimizer config
    opt = MOGAOptimizer()
    opt.objective = multi_objective
    opt.pool_size = pool_size
    opt.dominance_func = dominance_func
    opt_id = format(opt.__class__.__name__)
    item = (opt_id, opt)
    optimizers.append(item)

    # LLC optimizer config with different prediction windows
    # max_prediction_window = 3
    # for window in range(max_prediction_window + 1):
    # for window in [1, 2]:
    for window in [1]:
        opt = LLCOptimizer()
        opt.prediction_window = window
        opt.pool_size = pool_size
        opt.dominance_func = dominance_func
        opt.objective = multi_objective

        # Set plan finder algorithm
        # opt.plan_finder_class = plan_finder.GAPlanFinder
        # opt.plan_finder_class = plan_finder.ExhaustivePlanFinder
        opt.plan_finder_class = plan_finder.EmptyPlanFinder

        # Set environment forecasting
        seasonal_period = int(round(1 * 24 * 60 * 60 / float(step_time)))  # Seasonal of 1 day
        env_predictor = DefaultEnvironmentPredictor()
        env_predictor.net_predictor_class = AutoARIMAPredictor
        env_predictor.net_predictor_params = {'arima_params': {'seasonal': True, 'm': seasonal_period}}
        opt.environment_predictor = env_predictor

        opt_id = '{}_w{}'.format(opt.__class__.__name__, window)
        item = (opt_id, opt)
        # optimizers.append(item)

    # Execute simulation for each optimizer nb_runs times
    # nb_runs = 30
    nb_runs = 1
    for run in range(nb_runs):
        for (opt_id, opt) in optimizers:
            output_path = 'output/san_francisco/exp/{}/{}/'.format(run, opt_id)
            try:
                os.makedirs(output_path)
            except OSError:
                pass

            # Set simulation parameters
            sim = Simulator(scenario=scenario)
            sim.set_time(stop=stop_time, start=start_time, step=step_time)
            sim.optimizer = opt
            sim.monitor = ControlMonitor(metrics_func=metrics, output_path=output_path)

            # Run simulation
            perf_count = time.perf_counter()
            sim.run()
            elapsed_time = time.perf_counter() - perf_count
            print('run {}, opt {} - sim exec time: {}s'.format(run, opt_id, elapsed_time))


if __name__ == '__main__':
    main()
