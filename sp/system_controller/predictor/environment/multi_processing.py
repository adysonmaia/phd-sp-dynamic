from .environment import EnvironmentPredictor
from sp.core.predictor import AutoARIMAPredictor, SimpleExpSmoothingPredictor, NaivePredictor
from sp.core.model import EnvironmentInput
from collections import defaultdict
import multiprocessing as mp
import time
import logging


class MultiProcessingEnvironmentPredictor(EnvironmentPredictor):
    def __init__(self):
        EnvironmentPredictor.__init__(self)
        self.system = None
        self.environment_input = None

        self.load_predictor_class = None
        self.load_predictor_params = None
        self._load_data = None

        self.net_delay_predictor_class = None
        self.net_delay_predictor_params = None
        self._net_delay_data = None

        self.pool_size = 0
        self._pool = None
        self._map_func = None

        self.init_params()

    def init_params(self):
        self.clear()
        if self.load_predictor_class is None:
            self.load_predictor_class = AutoARIMAPredictor
        if self.net_delay_predictor_class is None:
            self.load_predictor_class = SimpleExpSmoothingPredictor
        self._init_pool()

    def clear(self):
        self.system = None
        self.environment_input = None
        self._load_data = defaultdict(lambda: defaultdict(lambda: []))
        self._net_delay_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [])))
        self._clear_pool()

    def _init_pool(self):
        self._clear_pool()

        self._pool = None
        self._map_func = map
        if self.pool_size > 0:
            try:
                self.pool_size = min(self.pool_size, mp.cpu_count())
                self._pool = mp.Pool(self.pool_size)
                self._map_func = self._pool.map
            except:
                pass

    def _clear_pool(self):
        if self._pool is not None:
            self._pool.terminate()
            self._pool = None
            self._map_func = None

    def update(self, system, environment_input):
        self.system = system
        self.environment_input = environment_input

        total_elapsed_time = 0.0

        perf_count = time.perf_counter()
        self._update_load_data(system, environment_input)
        elapsed_time = time.perf_counter() - perf_count
        total_elapsed_time += elapsed_time
        logging.debug("{:15} {:9.3f}".format("load update", elapsed_time))

        perf_count = time.perf_counter()
        self._update_net_delay_data(system, environment_input)
        elapsed_time = time.perf_counter() - perf_count
        total_elapsed_time += elapsed_time
        logging.debug("{:15} {:9.3f}".format("net update", elapsed_time))

        logging.debug("{:15} {:9.3f}".format("total update", total_elapsed_time))

    def _update_load_data(self, system, environment_input):
        for app in system.apps:
            for node in system.nodes:
                datum = environment_input.get_generated_load(app.id, node.id)
                data = self._load_data[app.id][node.id]
                data.append(datum)

    def _update_net_delay_data(self, system, environment_input):
        for app in system.apps:
            for src_node in system.nodes:
                for dst_node in system.nodes:
                    datum = environment_input.get_net_delay(app.id, src_node.id, dst_node.id)
                    data = self._net_delay_data[app.id][src_node.id][dst_node.id]
                    data.append(datum)

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
        list_params = []
        map_func = self._map_func
        if self.load_predictor_class == NaivePredictor:
            map_func = map

        for app in self.system.apps:
            for src_node in self.system.nodes:
                data = self._load_data[app.id][src_node.id]
                params = {"app_id": app.id, "node_id": src_node.id,
                          "data": data, "steps": steps,
                          "predictor_class": self.load_predictor_class,
                          "predictor_params": self.load_predictor_params}
                list_params.append(params)

        predictions = list(map_func(_predict, list_params))
        for (params, values) in zip(list_params, predictions):
            app_id = params["app_id"]
            node_id = params["node_id"]
            for index in range(steps):
                env_inputs[index].generated_load[app_id][node_id] = values[index]

        return env_inputs

    def _predict_net_delay(self, env_inputs, steps):
        list_params = []
        map_func = self._map_func
        if self.net_delay_predictor_class == NaivePredictor:
            map_func = map

        for app in self.system.apps:
            for src_node in self.system.nodes:
                for dst_node in self.system.nodes:
                    data = self._net_delay_data[app.id][src_node.id][dst_node.id]
                    params = {"app_id": app.id, "src_node_id": src_node.id, "dst_node_id": dst_node.id,
                              "data": data, "steps": steps,
                              "predictor_class": self.net_delay_predictor_class,
                              "predictor_params": self.net_delay_predictor_params}
                    list_params.append(params)

        predictions = list(map_func(_predict, list_params))
        for (params, values) in zip(list_params, predictions):
            app_id = params["app_id"]
            src_node_id = params["src_node_id"]
            dst_node_id = params["dst_node_id"]
            for index in range(steps):
                env_inputs[index].net_delay[app_id][src_node_id][dst_node_id] = values[index]

        for index in range(steps):
            env_inputs[index].net_path = self.environment_input.net_path

        return env_inputs


def _predict(params):
    data = params["data"]
    steps = params["steps"]
    predictor = None
    predictor_class = AutoARIMAPredictor
    predictor_params = {}
    if params["predictor_class"] is not None:
        predictor_class = params["predictor_class"]
    if params["predictor_params"] is not None:
        predictor_params.update(params["predictor_params"])
    predictor = predictor_class(**predictor_params)

    predictor.update(data)
    values = predictor.predict(steps)
    values = list(map(lambda v: max(0.0, v), values))
    return values
