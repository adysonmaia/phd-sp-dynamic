from . import Controller
from sp.model.environment import Environment
from sp.coverage.min_dist import MinDistCoverage
from sp.routing.shortest_path import ShortestPathRouting
from sp.estimator.link_delay import DefaultLinkDelayEstimator
from sp.estimator.request_load import DefaultRequestLoadEstimator
from sp.estimator.queue_size import DefaultQueueSizeEstimator
from abc import abstractmethod


class EnvironmentController(Controller):
    @abstractmethod
    def update(self, system):
        pass


class DefaultEnvironmentController(EnvironmentController):
    def __init__(self):
        EnvironmentController.__init__(self)
        self.routing = None
        self.coverage = None
        self.link_delay_estimator = None
        self.req_load_estimator = None
        self.queue_size_estimator = None

    def init_params(self, system):
        EnvironmentController.init_params(self, system)

        if self.coverage is None:
            self.coverage = MinDistCoverage()

        if self.link_delay_estimator is None:
            self.link_delay_estimator = DefaultLinkDelayEstimator()

        if self.routing is None:
            self.routing = ShortestPathRouting()
            self.routing.link_delay_estimator = self.link_delay_estimator
            self.routing.static_routing = True

        if self.req_load_estimator is None:
            self.req_load_estimator = DefaultRequestLoadEstimator()
        self.req_load_estimator.system = self.system

        if self.queue_size_estimator is None:
            self.queue_size_estimator = DefaultQueueSizeEstimator()
        self.queue_size_estimator.system = self.system

    def update(self, system):
        self.system = system
        env = Environment()

        self._update_mobility(env)
        self._update_coverage(env)
        self._update_request_load(env)
        self._update_app_queue_size(env)
        self._update_routing(env)

        return env

    def _update_mobility(self, env_model):
        for user in self.system.users:
            user.update_position(self.system.time)

    def _update_coverage(self, env_model):
        self.coverage.update(self.system)

    def _update_request_load(self, env_model):
        env_model.request_load = self.req_load_estimator.calc_all_loads(self.system)

    def _update_app_queue_size(self, env_model):
        env_model.app_queue_size = self.queue_size_estimator.calc_all_queue_sizes(self.system)

    def _update_routing(self, env_model):
        self.routing.update(self.system)
        env_model.net_delay = self.routing.get_all_paths_length()
        env_model.net_path = self.routing.get_all_paths()
