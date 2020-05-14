from .environment import EnvironmentPredictor
from sp.core.predictor import AutoARIMAPredictor, SimpleExpSmoothingPredictor
from sp.core.model import EnvironmentInput
from collections import defaultdict
from future.utils import iteritems
import time
import logging


class DefaultEnvironmentPredictor(EnvironmentPredictor):
    def __init__(self):
        EnvironmentPredictor.__init__(self)
        self.system = None
        self.environment_input = None
        self.load_predictor_class = None
        self.load_predictor_params = None
        self.load_predictor = None
        self.net_delay_predictor_class = None
        self.net_delay_predictor_params = None
        self.net_delay_predictor = None

        self.init_params()

    def init_params(self):
        self.system = None
        self.environment_input = None
        self.load_predictor = defaultdict(lambda: defaultdict(lambda: None))
        self.net_delay_predictor = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None)))

    def clear(self):
        self.system = None
        self.environment_input = None
        self._clear_load_predictor()
        self._clear_net_delay_predictor()

    def _clear_load_predictor(self):
        for (app_id, app_predictors_dict) in iteritems(self.load_predictor):
            for (node_id, predictor) in iteritems(app_predictors_dict):
                if predictor is not None:
                    predictor.clear()

    def _clear_net_delay_predictor(self):
        for (app_id, app_predictors_dict) in iteritems(self.net_delay_predictor):
            for (src_node_id, src_node_predictors_dict) in iteritems(app_predictors_dict):
                for (dst_node_id, predictor) in iteritems(src_node_predictors_dict):
                    if predictor is not None:
                        predictor.clear()

    def update(self, system, environment_input):
        self.system = system
        self.environment_input = environment_input

        total_elapsed_time = 0.0

        perf_count = time.perf_counter()
        self._update_load_predictor(system, environment_input)
        elapsed_time = time.perf_counter() - perf_count
        total_elapsed_time += elapsed_time
        logging.debug("{:15} {:9.3f}".format("load update", elapsed_time))

        perf_count = time.perf_counter()
        self._update_net_delay_predictor(system, environment_input)
        elapsed_time = time.perf_counter() - perf_count
        total_elapsed_time += elapsed_time
        logging.debug("{:15} {:9.3f}".format("net update", elapsed_time))

        logging.debug("{:15} {:9.3f}".format("total update", total_elapsed_time))

    def _update_load_predictor(self, system, environment_input):
        for app in system.apps:
            for node in system.nodes:
                value = environment_input.get_generated_load(app.id, node.id)

                # TODO: each application can specify its own predictor
                if self.load_predictor[app.id][node.id] is None:
                    predictor_class = AutoARIMAPredictor
                    predictor_params = {}
                    if self.load_predictor_class is not None:
                        predictor_class = self.load_predictor_class
                    if self.load_predictor_params is not None:
                        predictor_params.update(self.load_predictor_params)
                    self.load_predictor[app.id][node.id] = predictor_class(**predictor_params)

                predictor = self.load_predictor[app.id][node.id]
                predictor.update(value)

    def _update_net_delay_predictor(self, system, environment_input):
        for app in system.apps:
            for src_node in system.nodes:
                for dst_node in system.nodes:
                    value = environment_input.get_net_delay(app.id, src_node.id, dst_node.id)

                    if self.net_delay_predictor[app.id][src_node.id][dst_node.id] is None:
                        predictor_class = SimpleExpSmoothingPredictor
                        predictor_params = {}
                        if self.net_delay_predictor_class is not None:
                            predictor_class = self.net_delay_predictor_class
                        if self.net_delay_predictor_params is not None:
                            predictor_params.update(self.net_delay_predictor_params)
                        self.net_delay_predictor[app.id][src_node.id][dst_node.id] = predictor_class(**predictor_params)

                    predictor = self.net_delay_predictor[app.id][src_node.id][dst_node.id]
                    predictor.update(value)

    def predict(self, steps=1):
        envs = [EnvironmentInput.create_empty(self.system) for _ in range(steps)]
        total_elapsed_time = 0.0

        perf_count = time.perf_counter()
        envs = self._predict_load(envs, steps)
        elapsed_time = time.perf_counter() - perf_count
        total_elapsed_time += elapsed_time
        logging.debug("{:15} {:9.3f}".format("load predict", elapsed_time))

        perf_count = time.perf_counter()
        envs = self._predict_net_delay(envs, steps)
        elapsed_time = time.perf_counter() - perf_count
        total_elapsed_time += elapsed_time
        logging.debug("{:15} {:9.3f}".format("net predict", elapsed_time))

        logging.debug("{:15} {:9.3f}".format("total predict", total_elapsed_time))

        return envs

    def _predict_load(self, env_inputs, steps):
        for app in self.system.apps:
            for src_node in self.system.nodes:
                predictor = self.load_predictor[app.id][src_node.id]
                values = predictor.predict(steps)
                values = list(map(lambda v: max(0.0, v), values))
                for index in range(steps):
                    env_inputs[index].generated_load[app.id][src_node.id] = values[index]

        return env_inputs

    def _predict_net_delay(self, env_inputs, steps):
        for app in self.system.apps:
            for src_node in self.system.nodes:
                for dst_node in self.system.nodes:
                    predictor = self.net_delay_predictor[app.id][src_node.id][dst_node.id]
                    values = predictor.predict(steps)
                    values = list(map(lambda v: max(0.0, v), values))
                    for index in range(steps):
                        env_inputs[index].net_delay[app.id][src_node.id][dst_node.id] = values[index]

        for index in range(steps):
            env_inputs[index].net_path = self.environment_input.net_path

        return env_inputs