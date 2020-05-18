from .monitor import Monitor
from sp.system_controller import util
import time
import os
import json


class OptimizerMonitor(Monitor):
    """Simulation Monitor for Optimizer Events

    Attributes:
        metrics_func (list): list of metric functions
        output_path (str): path to save the logs
    """

    def __init__(self, metrics_func, output_path=None):
        """Initialization

        Args:
             metrics_func (list): list of metric functions
             output_path (str): path to save the logs
        """
        Monitor.__init__(self)
        self.metrics_func = metrics_func  # metric functions
        self.output_path = output_path

        self._metrics_data = list()  # log of metric data
        self._control_data = dict()  # log of control data
        self._perf_count = 0  # last performance count

    def on_sim_started(self, sim_time):
        """Event dispatched when the simulation started

        Args:
            sim_time (float): current simulation time
        """
        self._metrics_data.clear()
        self._control_data = {'place': [], 'alloc': [], 'ld': []}
        self._perf_count = 0

    def on_sys_ctrl_started(self, sim_time, system, environment_input):
        """Event dispatched when the system controller update started

        Args:
            sim_time (float): current simulation time
            system (sp.core.model.system.System): current system state
            environment_input (sp.core.model.environment_input.EnvironmentInput): current environment input
        """
        self._perf_count = time.perf_counter()

    def on_sys_ctrl_ended(self, sim_time, system, control_input, environment_input):
        """Event dispatched when the system controller update ended

        Args:
            sim_time (float): current simulation time
            system (sp.core.model.system.System): current system state
            control_input (sp.core.model.control_input.ControlInput): new control input after the controller update
            environment_input (sp.core.model.environment_input.EnvironmentInput): current environment input
        """
        opt_name = self.simulator.optimizer.__class__.__name__
        elapsed_time = time.perf_counter() - self._perf_count
        valid = util.is_solution_valid(system, control_input, environment_input)
        datum = {'time': sim_time, 'opt': opt_name, 'elapsed_time': elapsed_time, 'valid': valid}
        for func in self.metrics_func:
            key = func.__name__
            value = func(system, control_input, environment_input)
            datum[key] = value
        self._metrics_data.append(datum)

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

        self._control_data['place'] += place_datum
        self._control_data['ld'] += ld_datum
        self._control_data['alloc'] += alloc_datum

    def on_sim_ended(self, sim_time):
        """Event dispatched when the simulation ended

        Args:
            sim_time (float): current simulation time
        """
        if self.output_path is None:
            return

        try:
            os.makedirs(self.output_path)
        except OSError:
            pass

        metrics_filename = os.path.join(self.output_path, 'metrics.json')
        place_filename = os.path.join(self.output_path, 'placement.json')
        alloc_filename = os.path.join(self.output_path, 'allocation.json')
        ld_filename = os.path.join(self.output_path, 'load_distribution.json')

        files_data = [
            (metrics_filename, self._metrics_data),
            (place_filename, self._control_data['place']),
            (alloc_filename, self._control_data['alloc']),
            (ld_filename, self._control_data['ld']),
        ]

        for (filename, data) in files_data:
            with open(filename, 'w') as file:
                json.dump(data, file, indent=2)
