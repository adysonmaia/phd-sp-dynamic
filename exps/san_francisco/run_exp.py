from sp.core.model import Scenario
from sp.simulator import Simulator, Monitor
from sp.system_controller.optimizer.dynamic import LLCOptimizer
from sp.system_controller.optimizer.static import SOGAOptimizer, MOGAOptimizer, CloudOptimizer
from sp.system_controller import metric
from datetime import datetime
from pytz import timezone
import json
import time
import os


UTC_TZ = timezone('UTC')
SF_TZ_STR = 'US/Pacific'
SF_TZ = timezone(SF_TZ_STR)


class ControlMonitor(Monitor):
    """Simulation monitor
    """
    def __init__(self, metrics_func, output_path):
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

        datum = {'time': sim_time, 'opt': opt_name, 'elapsed_time': elapsed_time}
        for func in self.metrics_func:
            key = func.__name__
            value = func(system, control_input, environment_input)
            datum[key] = value
        self.metrics_data.append(datum)
        print(datum)
        print("--")

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

    def on_sim_ended(self, sim_time):
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
    filename = 'input/san_francisco/scenario.json'
    scenario = None
    with open(filename) as json_file:
        data = json.load(json_file)
        scenario = Scenario.from_json(data)

    # Set simulation time
    start_time = SF_TZ.localize(datetime(2008, 5, 24, 0, 0, 0)).timestamp()
    stop_time = SF_TZ.localize(datetime(2008, 5, 24, 23, 59, 59)).timestamp()
    # step_time = 10 * 60  # seconds or 10 min
    step_time = 60 * 60  # seconds or 1H

    # Set optimizer solution
    objective = [
        metric.deadline.max_deadline_violation,
        metric.cost.overall_cost,
        metric.availability.avg_unavailability,
        metric.migration.overall_migration_cost
    ]
    # opt = CloudOptimizer()
    # opt = SOGAOptimizer()
    # opt = MOGAOptimizer()
    opt = LLCOptimizer()
    opt.prediction_window = 3
    opt.max_iterations = 100
    opt.pool_size = 6
    opt.objective = objective

    output_path = 'output/san_francisco/exp/{}/'.format(opt.__class__.__name__)
    try:
        os.makedirs(output_path)
    except OSError:
        pass

    # Set simulation parameters
    sim = Simulator(scenario=scenario)
    sim.set_time(stop=stop_time, start=start_time, step=step_time)
    sim.optimizer = opt
    sim.monitor = ControlMonitor(metrics_func=objective, output_path=output_path)

    # Run simulation
    perf_count = time.perf_counter()
    sim.run()
    elapsed_time = time.perf_counter() - perf_count
    print('sim exec time: {}s'.format(elapsed_time))


if __name__ == '__main__':
    main()