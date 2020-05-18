from sp.core.model import Scenario
from sp.core.predictor import AutoARIMAPredictor, NaivePredictor
from sp.simulator import Simulator
from sp.simulator.monitor import OptimizerMonitor
from sp.system_controller import metric, util
from sp.system_controller.optimizer.llc import LLCOptimizer, plan_finder, input_finder
from sp.system_controller.optimizer import SOGAOptimizer, MOGAOptimizer, CloudOptimizer, SOHeuristicOptimizer
from sp.system_controller.predictor import MultiProcessingEnvironmentPredictor
import json
import math
import os
import time


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

        time_slot = (sim_time - self.simulator.start_time) / float(self.simulator.step_time)
        time_slot = int(math.floor(time_slot)) + 1
        total_time_slot = (self.simulator.stop_time - self.simulator.start_time) / float(self.simulator.step_time)
        total_time_slot = int(math.floor(total_time_slot)) + 1

        datum = self._metrics_data[-1]
        elapsed_time = datum['elapsed_time']

        print_prefix = '{}: '.format(self.debug_prefix) if self.debug_prefix else ''
        print('{}{}/{} - {:9.3f}s'.format(print_prefix, time_slot, total_time_slot, elapsed_time))
        print(datum)

        print(' ')
        for app in system.apps:
            places = [n.id for n in system.nodes if control_input.get_app_placement(app.id, n.id)]
            load = sum([util.calc_load_before_distribution(app.id, node.id, system, environment_input)
                        for node in system.nodes])
            deadline_violation = util.filter_metric(metric.deadline.overall_deadline_violation,
                                                    system, control_input, environment_input,
                                                    apps_id=app.id)
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
    # pool_size = 0
    timeout = 3 * 60  # 3 min

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
    optimizers.append(item)

    # LLC (control input and plan) finders versions
    llc_finders = [
        {
            'key': 'ssga',
            'input': input_finder.SSGAInputFinder,
            'input_params': {'timeout': timeout},
            'plan': None
        },
        {
            'key': 'sga',
            'input': input_finder.SGAInputFinder,
            'input_params': {'timeout': timeout},
            'plan': None
        },
        # {
        #     'key': 'mga',
        #     'input': input_finder.MGAInputFinder,
        #     'input_params': {'timeout': timeout},
        #     'plan': plan_finder.GAPlanFinder,
        #     'plan_params': {'timeout': timeout},
        # },
    ]

    # LLC optimizer with different parameters
    prediction_windows = [0, 1, 2]
    # prediction_windows = [0, 1]
    # prediction_windows = [1]
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
            env_predictor = MultiProcessingEnvironmentPredictor()
            env_predictor.pool_size = pool_size
            env_predictor.load_predictor_class = AutoARIMAPredictor
            env_predictor.load_predictor_params = {'max_p': 3, 'max_q': 3, 'stepwise': True, 'maxiter': 10}
            env_predictor.net_delay_predictor_class = NaivePredictor
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
            sim.monitor = ExpRunMonitor(metrics_func=metrics, output_path=output_path, debug_prefix=debug_prefix)

            # Run simulation
            perf_count = time.perf_counter()
            sim.run()
            elapsed_time = time.perf_counter() - perf_count
            print('scenario {}, run {}, opt {} - sim exec time: {}s'.format(scenario_id, run, opt_id, elapsed_time))
            print('-' * 10)


if __name__ == '__main__':
    main()
