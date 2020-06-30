from .environment import EnvironmentPredictor
from sp.core.model import EnvironmentInput, System
from sp.core.util import json_util
from collections import defaultdict


class RealDataEnvironmentPredictor(EnvironmentPredictor):
    """Real Data Environment Predictor

    Attributes:
        system (System): last system's state
        environment_input (EnvironmentInput): last environment input
    """

    def __init__(self):
        """Initialization
        """
        EnvironmentPredictor.__init__(self)

        self.system = None
        self.environment_input = None

        self._load_data = None
        self._net_delay_data = None
        self._load_raw_data = None
        self._net_delay_raw_data = None
        self._current_index = 0

    def init_params(self):
        """Initialize parameters for the simulation
        """
        self.clear()
        self._init_load_data()
        self._init_net_delay_data()

    def clear(self):
        """Clear parameters
        """
        self._current_index = 0
        self.system = None
        self.environment_input = None
        self._load_data = defaultdict(lambda: defaultdict(lambda: []))
        self._net_delay_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [])))

    @property
    def load_data(self):
        """Get the real load data for the entire time series

        Returns:
            dict(dict(list)): data list indexed by app's id, node's id
        """
        return self._load_data

    @load_data.setter
    def load_data(self, data):
        """Set the real load data for the entire time series.
        E.g.:

            .. code-block:: python

                # Using a list
                data = [
                    {'time': 0, 'app': 0, 'node': 0, 'load': 1.5},
                    {'time': 1, 'app': 0, 'node': 0, 'load': 2.5}
                ]
                predictor = RealDataEnvironmentPredictor()
                predictor.load_data = data

                # Or using a file
                filename = 'path/load.json'
                predictor.load_data = filename

        Args:
            data (Union[str,dict]): data in json format or data file name
        """
        self._load_raw_data = data

    @property
    def net_delay_data(self):
        """Get the real network delay data for the entire time series

        Returns:
            dict(dict(dict(list))): data list indexed by app's id, src node's id, dst node's id
        """
        return self._net_delay_data

    @net_delay_data.setter
    def net_delay_data(self, data):
        """Set the real network delay data for the entire time series.
        E.g.:

             .. code-block:: python

                # Using a list
                data = [
                    {'time': 0, 'app': 0, 'src_node': 0, 'dst_node': 1, 'net_delay': 1.5},
                    {'time': 1, 'app': 0, 'src_node': 0, 'dst_node': 1, 'net_delay': 2.5}
                ]
                predictor = RealDataEnvironmentPredictor()
                predictor.net_delay_data = data

                # Or using a file
                filename = 'path/net_delay.json'
                predictor.net_delay_data = filename

        Args:
            data (Union[str,dict]): data in json format or data file name
        """
        self._net_delay_raw_data = data

    def _init_load_data(self):
        """Initialize load data
        """
        if self._load_raw_data is None:
            return

        json_data = json_util.load_content(self._load_raw_data)
        for row in json_data:
            app_id = int(row['app'])
            node_id = int(row['node'])
            load = float(row['load'])
            self._load_data[app_id][node_id].append(load)

    def _init_net_delay_data(self):
        """Initialize net delay data
        """
        if self._net_delay_raw_data is None:
            return

        json_data = json_util.load_content(self._net_delay_raw_data)
        for row in json_data:
            app_id = int(row['app'])
            src_node_id = int(row['src_node'])
            dst_node_id = int(row['dst_node'])
            net_delay = float(row['net_delay'])
            self._net_delay_data[app_id][src_node_id][dst_node_id].append(net_delay)

    def update(self, system, environment_input):
        """Update predictor at a simulation time with a system's state and environment input

        Args:
            system (System): system's state
            environment_input (EnvironmentInput): environment input
        """
        self.system = system
        self.environment_input = environment_input
        self._current_index += 1

    def predict(self, steps=1):
        """Predict next environment inputs

        Args:
            steps (int): number of values to predict
        Returns:
            list(EnvironmentInput): predicted data
        """
        envs = [EnvironmentInput.create_empty(self.system) for _ in range(steps)]
        envs = self._predict_load(envs)
        envs = self._predict_net_delay(envs)
        return envs

    def _predict_load(self, env_inputs):
        """Predict load attribute of next environment inputs

        Args:
            env_inputs list(EnvironmentInput): next environment inputs
        Returns:
            list(EnvironmentInput): predicted data
        """
        for app in self.system.apps:
            for node in self.system.nodes:
                data = self._load_data[app.id][node.id]
                for step in range(len(env_inputs)):
                    data_index = step + self._current_index + 1
                    value = None
                    if data_index < len(data):
                        value = data[data_index]
                    else:
                        value = self.environment_input.generated_load[app.id][node.id]
                    env_inputs[step].generated_load[app.id][node.id] = value
        return env_inputs

    def _predict_net_delay(self, env_inputs):
        """Predict network delay attribute of next environment inputs

        Args:
            env_inputs list(EnvironmentInput): next environment inputs
        Returns:
            list(EnvironmentInput): predicted data
        """
        for app in self.system.apps:
            for src_node in self.system.nodes:
                for dst_node in self.system.nodes:
                    data = self._net_delay_data[app.id][src_node.id][dst_node.id]
                    for step in range(len(env_inputs)):
                        data_index = step + self._current_index + 1
                        value = None
                        if data_index < len(data):
                            value = data[data_index]
                        else:
                            value = self.environment_input.net_delay[app.id][src_node.id][dst_node.id]
                        env_inputs[step].net_delay[app.id][src_node.id][dst_node.id] = value
                        env_inputs[step].net_path = self.environment_input.net_path
        return env_inputs


