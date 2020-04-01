from sp.core.model import Scenario
from sp.simulator import Simulator, Monitor
from sp.system_controller.optimizer.dynamic import LLCOptimizer
from sp.system_controller.optimizer.static import SOGAOptimizer, MOGAOptimizer, CloudOptimizer, SOHeuristicOptimizer
from sp.system_controller import metric
from sp.system_controller.utils import is_solution_valid, pareto_dominates, preferred_dominates
from sp.system_controller.utils import calc_load_before_distribution
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


def _calc_delta_time(system, control_input, environment_input):
    from sp.system_controller.estimator import DefaultProcessingEstimator
    proc_estimator = DefaultProcessingEstimator()

    delta = []
    for app in system.apps:
        for dst_node in system.nodes:
            if not control_input.get_app_placement(app.id, dst_node.id):
                continue

            proc_result = proc_estimator(app.id, dst_node.id,
                                         system=system,
                                         control_input=control_input,
                                         environment_input=environment_input)
            proc_delay = proc_result.delay

            for src_node in system.nodes:
                ld = control_input.get_load_distribution(app.id, src_node.id, dst_node.id)
                load = calc_load_before_distribution(app.id, src_node.id, system, environment_input)
                load = load * ld
                if load > 0.0:
                    net_delay = environment_input.get_net_delay(app.id, src_node.id, dst_node.id)
                    delay = net_delay + proc_delay
                    delta.append(delay - app.deadline)
                    if delay > app.deadline:
                        print('app {}, dst {}, src {}: {} + {} > {}'.format(app.id, dst_node.id, src_node.id,
                                                                            net_delay, proc_delay, app.deadline))
    return delta


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

        valid = is_solution_valid(system, control_input, environment_input)
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
                # print(item)

                item = {'time': sim_time, 'app': app.id, 'node': dst_node.id}
                for resource in system.resources:
                    value = control_input.get_allocated_resource(app.id, dst_node.id, resource.name)
                    item[resource.name] = value
                alloc_datum.append(item)

                for src_node in system.nodes:
                    value = control_input.get_load_distribution(app.id, src_node.id, dst_node.id)
                    item = {'time': sim_time, 'app': app.id,
                            'dst_node': dst_node.id, 'src_node': src_node.id, 'ld': value}
                    ld_datum.append(item)

        self.control_data['place'] += place_datum
        self.control_data['ld'] += ld_datum
        self.control_data['alloc'] += alloc_datum

        for app in system.apps:
            places = [n.id for n in system.nodes if control_input.get_app_placement(app.id, n.id)]
            print(app.id, app.type, len(places), places)

        # for node in system.nodes:
        #     resource_name = 'CPU'
        #     alloc = [control_input.get_allocated_resource(app.id, node.id, resource_name) for app in system.apps]
        #     alloc = sum(alloc)
        #     capacity = node.capacity[resource_name]
        #     available = capacity - alloc
        #     if alloc > 0.0:
        #         print('node {}, rsc {}, cap {}, alloc {}, free {}'.format(node.id, resource_name,
        #                                                                            capacity, alloc, available))

        for app in system.apps:
            users = environment_input.get_attached_users()
            user = list(filter(lambda u: u.app_id == app.id and u.node_id is not None, users))
            count = len(user)
            print('app {} {}, users {}'.format(app.id, app.type, count))

        # for app in system.apps:
        #     for src_node in system.nodes:
        #         load = environment_input.get_generated_load(app.id, src_node.id)
        #         print('app {} {}, node {}, gen load {}'.format(app.id, app.type, src_node.id, load))

        # for app in system.apps:
        #     for src_node in system.nodes:
        #         for dst_node in system.nodes:
        #             ld = control_input.get_load_distribution(app.id, src_node.id, dst_node.id)
        #             load_before = calc_load_before_distribution(app.id, src_node.id, system, environment_input)
        #             load_after = load_before * ld
        #             if load_after > 0.0 and src_node != dst_node:
        #                 print('app {} {}, src {}, dst {}, {} * {} = load {}'.format(app.id, app.type,
        #                                                                             src_node.id, dst_node.id,
        #                                                                             ld, load_before, load_after))

        # _calc_delta_time(system, control_input, environment_input)
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

        for (filename, data) in files_data:
            with open(filename, 'w') as file:
                json.dump(data, file, indent=2)


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
    # step_time = 10 * 60  # seconds or 10 min
    step_time = 60 * 60  # seconds or 1H

    # Set optimizer solutions
    optimizers = []
    objective = [
        metric.deadline.max_deadline_violation,
        metric.cost.overall_cost,
        # metric.availability.avg_unavailability,
        metric.migration.overall_migration_cost
    ]
    metrics = [
        metric.deadline.max_deadline_violation,
        metric.cost.overall_cost,
        metric.availability.avg_unavailability,
        metric.migration.overall_migration_cost
    ]
    # dominance_func = pareto_dominates
    dominance_func = preferred_dominates
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
    opt.objective = metric.deadline.max_deadline_violation
    opt_id = opt.__class__.__name__
    item = (opt_id, opt)
    # optimizers.append(item)

    # Multi-Objective GA optimizer config
    opt = MOGAOptimizer()
    opt.objective = objective
    opt.pool_size = pool_size
    opt.dominance_func = dominance_func
    opt_id = opt.__class__.__name__
    item = (opt_id, opt)
    optimizers.append(item)

    # LLC optimizer config with different prediction windows
    # max_prediction_window = 3
    max_prediction_window = 0
    for window in range(max_prediction_window + 1):
        opt = LLCOptimizer()
        opt.prediction_window = window
        opt.max_iterations = 100
        opt.pool_size = pool_size
        opt.dominance_func = dominance_func
        opt.objective = objective
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
