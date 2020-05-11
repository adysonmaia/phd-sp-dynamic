from sp.core.model import Scenario
from sp.core.predictor import AutoARIMAPredictor, ARIMAPredictor
from sp.simulator import Simulator, Monitor
from sp.system_controller import metric, util
from sp.system_controller.optimizer.llc import LLCOptimizer, plan_finder, input_finder
from sp.system_controller.optimizer import SOGAOptimizer, MOGAOptimizer, CloudOptimizer, SOHeuristicOptimizer
from sp.system_controller.predictor import DefaultEnvironmentPredictor
import json
import math
import os
import time
import logging
logging.basicConfig(level=logging.DEBUG)


def get_app_deadline_violation(app, system, control_input, environment_input):
    violation = 0.0
    for dst_node in system.nodes:
        if not control_input.get_app_placement(app.id, dst_node.id):
            continue

        for src_node in system.nodes:
            load = util.calc_load_after_distribution(app.id, src_node.id, dst_node.id,
                                                     system, control_input, environment_input)
            if load > 0.0:
                rt = util.calc_response_time(app.id, src_node.id, dst_node.id,
                                             system, control_input, environment_input)
                if rt > app.deadline:
                    violation += rt - app.deadline

                    # if app.type == 'EMBB':
                    #     ld = control_input.get_load_distribution(app.id, src_node.id, dst_node.id)
                    #     net_delay = util.calc_network_delay(app.id, src_node.id, dst_node.id,
                    #                                         system, control_input, environment_input)
                    #     proc_delay = util.calc_processing_delay(app.id, dst_node.id,
                    #                                             system, control_input, environment_input)
                    #     init_delay = util.calc_initialization_delay(app.id, dst_node.id,
                    #                                                 system, control_input, environment_input)
                    #     print('app {:3d}, src {:3d}, dst {:3d}, '
                    #           'load {:9.3f}, ld {:6.3f}, '
                    #           'net {:6.3f}, proc {:6.3f}, init {:6.3f}, '
                    #           'rt {:6.3f}, deadline {:6.3f}'.format(
                    #         app.id, src_node.id, dst_node.id,
                    #         load, ld,
                    #         net_delay, proc_delay, init_delay,
                    #         rt, app.deadline
                    #     ))
    return violation


class ControlMonitor(Monitor):
    """Simulation monitor
    """
    def __init__(self, metrics_func, output_path=None, debug_prefix=None):
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
        self.debug_prefix = debug_prefix

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

        time_slot = (sim_time - self.simulator.start_time) / float(self.simulator.step_time)
        time_slot = int(math.floor(time_slot)) + 1
        total_time_slot = (self.simulator.stop_time - self.simulator.start_time) / float(self.simulator.step_time)
        total_time_slot = int(math.floor(total_time_slot)) + 1

        print_prefix = '{}: '.format(self.debug_prefix) if self.debug_prefix else ''
        print('{}{}/{} - {}s'.format(print_prefix, time_slot, total_time_slot, elapsed_time))

        valid = util.is_solution_valid(system, control_input, environment_input)
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
                    load = util.calc_load_before_distribution(app.id, src_node.id, system, environment_input)
                    ld = control_input.get_load_distribution(app.id, src_node.id, dst_node.id)
                    item = {'time': sim_time, 'app': app.id,
                            'src_node': src_node.id, 'dst_node': dst_node.id, 'ld': ld, 'load': load}
                    ld_datum.append(item)

        self.control_data['place'] += place_datum
        self.control_data['ld'] += ld_datum
        self.control_data['alloc'] += alloc_datum

        for app in system.apps:
            places = [n.id for n in system.nodes if control_input.get_app_placement(app.id, n.id)]
            load = sum([util.calc_load_before_distribution(app.id, node.id, system, environment_input)
                        for node in system.nodes])
            deadline_violation = get_app_deadline_violation(app, system, control_input, environment_input)
            print('app {:2d} {:>5}, deadline {:6.1f}ms, max instances {:2d}, load {:10.3f}, '
                  'places {:2d}: {}, deadline violation {}s'.format(
                app.id, app.type, 1000 * app.deadline, app.max_instances, load,
                len(places), places, deadline_violation
            ))

        print(' ')
        for node in system.nodes:
            free_str = 'node {:2d}, '.format(node.id)
            for resource in system.resources:
                capacity = node.capacity[resource.name]
                alloc = sum([control_input.get_allocated_resource(a.id, node.id, resource.name) for a in system.apps])
                free = 1.0
                if capacity > 0.0 and not math.isinf(capacity):
                    free = (capacity - alloc) / float(capacity)
                    free = round(free, 3)
                free_str += '{} {:6.3f}, '.format(resource.name, free)
            print(free_str)

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
    # Load simulation parameters
    root_output_path = 'output/synthetic/exp/'
    simulation_filename = 'input/synthetic/simulation.json'
    simulation_data = None
    with open(simulation_filename) as json_file:
        simulation_data = json.load(json_file)

    time_start = simulation_data['time']['start']
    time_stop = simulation_data['time']['stop']
    time_step = simulation_data['time']['step']

    # Set objectives and metrics functions
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

    #
    dominance_func = util.preferred_dominates
    pool_size = 4
    # pool_size = 8
    # pool_size = 0
    timeout = 3 * 60  # 3 min

    # Set optimizer solutions

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
    opt.timeout = timeout
    opt_id = opt.__class__.__name__
    item = (opt_id, opt)
    # optimizers.append(item)

    # Multi-Objective GA optimizer config
    opt = MOGAOptimizer()
    opt.objective = multi_objective
    opt.pool_size = pool_size
    opt.timeout = timeout
    opt.dominance_func = dominance_func
    opt_id = format(opt.__class__.__name__)
    item = (opt_id, opt)
    # optimizers.append(item)

    # LLC (control input and plan) finders versions
    llc_finders = [
        {
            'key': 'ssga',
            'input': input_finder.SSGAInputFinder,
            'input_params': {'timeout': timeout},
            'plan': None
        },
        # {'input': input_finder.SGAInputFinder, 'plan': None, 'key': 'sga'},
    ]

    # LLC optimizer with different parameters
    # prediction_windows = [0, 1, 2]
    # prediction_windows = [0, 1]
    prediction_windows = [1]
    # prediction_windows = [0]
    for window in prediction_windows:
        for llc_finder in llc_finders:
            opt = LLCOptimizer()
            opt.prediction_window = window
            opt.pool_size = pool_size
            opt.dominance_func = dominance_func
            opt.objective = multi_objective
            opt.input_finder_class = llc_finder['input']
            opt.input_finder_params = llc_finder['input_params'] if 'input_params' in llc_finder else None
            opt.plan_finder_class = llc_finder['plan']
            opt.plan_finder_params = llc_finder['plan_params'] if 'plan_params' in llc_finder else None

            # Set environment forecasting
            env_predictor = DefaultEnvironmentPredictor()
            env_predictor.net_predictor_class = AutoARIMAPredictor
            env_predictor.net_predictor_params = {'maxiter': 2}
            # env_predictor.net_predictor_class = ARIMAPredictor
            opt.environment_predictor = env_predictor

            opt_id = '{}_{}_w{}'.format(opt.__class__.__name__, llc_finder['key'], window)
            item = (opt_id, opt)
            optimizers.append(item)

    # Create a simulation for each loaded scenario
    for scenario_data in simulation_data['scenarios']:
        scenario_filename = scenario_data['scenario']
        scenario_id = scenario_data['scenario_id']
        run = scenario_data['run']

        scenario = None
        with open(scenario_filename) as json_file:
            scenario_json = json.load(json_file)
            scenario = Scenario.from_json(scenario_json)

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
            sim = Simulator(scenario=scenario)
            sim.set_time(stop=time_stop, start=time_start, step=time_step)
            sim.optimizer = opt
            sim.monitor = ControlMonitor(metrics_func=metrics, output_path=output_path, debug_prefix=debug_prefix)

            # Run simulation
            perf_count = time.perf_counter()
            sim.run()
            elapsed_time = time.perf_counter() - perf_count
            print('scenario {}, run {}, opt {} - sim exec time: {}s'.format(scenario_id, run, opt_id, elapsed_time))
            print('-' * 10)


if __name__ == '__main__':
    main()
