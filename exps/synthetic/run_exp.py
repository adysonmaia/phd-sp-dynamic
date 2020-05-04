from sp.core.model import Scenario
from sp.core.predictor import AutoARIMAPredictor
from sp.simulator import Simulator, Monitor
from sp.system_controller import metric, util
from sp.system_controller.optimizer.llc import LLCOptimizer, plan_finder, input_finder
from sp.system_controller.optimizer import SOGAOptimizer, MOGAOptimizer, CloudOptimizer, SOHeuristicOptimizer
from sp.system_controller.predictor import DefaultEnvironmentPredictor
import json
import os
import time


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

        print('{} - {}s'.format(sim_time, elapsed_time))

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
            users = environment_input.get_attached_users()
            users = list(filter(lambda u: u.app_id == app.id and u.node_id is not None, users))
            deadline_violation = get_app_deadline_violation(app, system, control_input, environment_input)
            print('app {} {}, deadline {}ms, users {}, places {}: {}, deadline violation {}s'.format(
                app.id, app.type, 1000 * app.deadline, len(users), len(places), places, deadline_violation
            ))

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
    nb_bs = 25
    nb_apps = 10
    nb_users = 1000
    scenario_id = 'n{}_a{}_u{}'.format(nb_bs, nb_apps, nb_users)
    scenario_filename = 'input/synthetic/scenario_{}.json'.format(scenario_id)
    scenario = None
    with open(scenario_filename) as json_file:
        data = json.load(json_file)
        scenario = Scenario.from_json(data)

    time_start = 0
    time_end = 100
    time_step = 1

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

    dominance_func = util.preferred_dominates
    pool_size = 8
    # pool_size = 0

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
    # optimizers.append(item)

    # LLC (control input and plan) finders versions
    llc_finders = [
        {'input': input_finder.SSGAInputFinder, 'plan': None, 'key': 'ssga'},
        # {'input': input_finder.SGAInputFinder, 'plan': None, 'key': 'sga'},
    ]

    # LLC optimizer config with different parameters
    # prediction_windows = [0, 1, 2]
    prediction_windows = [1]
    for window in prediction_windows:
        for llc_finder in llc_finders:
            opt = LLCOptimizer()
            opt.prediction_window = window
            opt.pool_size = pool_size
            opt.dominance_func = dominance_func
            opt.objective = multi_objective
            opt.input_finder_class = llc_finder['input']
            opt.plan_finder_class = llc_finder['plan']

            # Set environment forecasting
            env_predictor = DefaultEnvironmentPredictor()
            env_predictor.net_predictor_class = AutoARIMAPredictor
            opt.environment_predictor = env_predictor

            opt_id = '{}_{}_w{}'.format(opt.__class__.__name__, llc_finder['key'], window)
            item = (opt_id, opt)
            optimizers.append(item)

    # Execute simulation for each optimizer nb_runs times
    # nb_runs = 30
    nb_runs = 1
    for run in range(nb_runs):
        for (opt_id, opt) in optimizers:
            output_path = 'output/synthetic/exp/{}/{}/{}/'.format(scenario_id, run, opt_id)
            try:
                os.makedirs(output_path)
            except OSError:
                pass

            # Set simulation parameters
            sim = Simulator(scenario=scenario)
            sim.set_time(stop=time_end, start=time_start, step=time_step)
            sim.optimizer = opt
            sim.monitor = ControlMonitor(metrics_func=metrics, output_path=output_path)

            # Run simulation
            perf_count = time.perf_counter()
            sim.run()
            elapsed_time = time.perf_counter() - perf_count
            print('run {}, opt {} - sim exec time: {}s'.format(run, opt_id, elapsed_time))


if __name__ == '__main__':
    main()
