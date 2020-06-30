from .monitor import Monitor
import os
import json


class EnvironmentMonitor(Monitor):
    """Simulation Monitor for Environment Events

    Attributes:
        output_path (str): path to save the logs
        log_net_delay (bool): whether to log net delay information or not
        log_load (bool): whether to log load information or not
        net_delay_log_filename (str): net delay log file name
        load_log_filename (str): load log file name
    """

    def __init__(self, output_path=None, log_net_delay=True, log_load=True):
        """Initialization

        Args:
             output_path (str): path to save the logs
        """
        Monitor.__init__(self)
        self.output_path = output_path
        self.log_net_delay = log_net_delay
        self.log_load = log_load

        self.net_delay_log_filename = 'net_delay.json'
        self.load_log_filename = 'load.json'

        self._net_delay_data = []
        self._load_data = []

    def on_sim_started(self, sim_time):
        """Event dispatched when the simulation started

        Args:
            sim_time (float): current simulation time
        """
        self._net_delay_data.clear()
        self._load_data.clear()

    def on_env_ctrl_ended(self, sim_time, system, environment_input):
        """Event dispatched when the environment controller update ended

        Args:
            sim_time (float): current simulation time
            system (sp.core.model.system.System): current system state
            environment_input (sp.core.model.environment_input.EnvironmentInput): current environment input
        """
        for app in system.apps:
            for src_node in system.nodes:
                load = environment_input.get_generated_load(app.id, src_node.id)
                nb_users = environment_input.get_nb_users(app.id, src_node.id)
                load_datum = {"time": sim_time, "app": app.id, "node": src_node.id, "load": load, "users": nb_users}
                self._load_data.append(load_datum)

                for dst_node in system.nodes:
                    net_delay = environment_input.get_net_delay(app.id, src_node.id, dst_node.id)
                    net_datum = {"time": sim_time, "app": app.id, "src_node": src_node.id, "dst_node": dst_node.id,
                                 "net_delay": net_delay}
                    self._net_delay_data.append(net_datum)

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

        net_delay_filename = os.path.join(self.output_path, self.net_delay_log_filename)
        load_filename = os.path.join(self.output_path, self.load_log_filename)
        files_data = []
        if self.log_net_delay:
            files_data.append((net_delay_filename, self._net_delay_data))
        if self.log_load:
            files_data.append((load_filename, self._load_data))

        for (filename, data) in files_data:
            with open(filename, 'w') as file:
                json.dump(data, file, indent=2)
