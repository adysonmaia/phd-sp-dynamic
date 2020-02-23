from . import Controller
from sp.model.environment import Environment
from sp.coverage.min_dist import MinDistCoverage
from sp.routing.shortest_path import ShortestPathRouting
from sp.estimator.link_delay import DefaultLinkDelayEstimator
from sp.estimator.request_load import DefaultRequestLoadEstimator
from sp.estimator.queue_size import DefaultQueueSizeEstimator


class EnvironmentController(Controller):
    def __init__(self):
        Controller.__init__(self)


class DefaultEnvironmentController(EnvironmentController):
    def __init__(self):
        EnvironmentController.__init__(self)
        self.routing = None
        self.coverage = None
        self.link_delay_estimator = None
        self.req_load_estimator = None
        self.queue_size_estimator = None

    def start(self, system):
        EnvironmentController.start(self, system)

        if self.coverage is None:
            self.coverage = MinDistCoverage()
        self.coverage.system = self.system

        if self.link_delay_estimator is None:
            self.link_delay_estimator = DefaultLinkDelayEstimator()
        self.link_delay_estimator.system = self.system

        if self.routing is None:
            self.routing = ShortestPathRouting()
            self.routing.link_delay_estimator = self.link_delay_estimator
            self.routing.static_routing = True
        self.routing.system = self.system

        if self.req_load_estimator is None:
            self.req_load_estimator = DefaultRequestLoadEstimator()
        self.req_load_estimator.system = self.system

        if self.queue_size_estimator is None:
            self.queue_size_estimator = DefaultQueueSizeEstimator()
        self.queue_size_estimator.system = self.system

    def update(self, time):
        env = Environment()

        self._update_mobility(time, env)
        self._update_coverage(time, env)
        self._update_request_load(time, env)
        self._update_app_queue_size(time, env)
        self._update_routing(time, env)

        self.system.environment = env

    def _update_mobility(self, time, env_model):
        for user in self.system.users:
            user.update_position(time)

    def _update_coverage(self, time, env_model):
        self.coverage.update(time)

    def _update_request_load(self, time, env_model):
        env_model.request_load = self.req_load_estimator.calc_all_loads()

    def _update_app_queue_size(self, time, env_model):
        env_model.app_queue_size = self.queue_size_estimator.calc_all_queue_sizes()

    def _update_routing(self, time, env_model):
        self.routing.update(time)
        env_model.net_delay = self.routing.get_all_paths_length()
        env_model.net_path = self.routing.get_all_paths()
