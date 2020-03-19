from sp.physical_system.coverage.min_distance import MinDistanceCoverage
from sp.physical_system.routing.shortest_path import ShortestPathRouting
from sp.physical_system.estimator import DefaultLinkDelayEstimator, DefaultGeneratedLoadEstimator
from sp.core.model import EnvironmentInput
import copy


class EnvironmentController:
    def __init__(self):
        self.routing = None
        self.coverage = None
        self.link_delay_estimator = None
        self.gen_load_estimator = None

    def start(self):
        if self.coverage is None:
            self.coverage = MinDistanceCoverage()

        if self.link_delay_estimator is None:
            self.link_delay_estimator = DefaultLinkDelayEstimator()

        if self.routing is None:
            self.routing = ShortestPathRouting()
            self.routing.link_delay_estimator = self.link_delay_estimator
            self.routing.static_routing = True

        if self.gen_load_estimator is None:
            self.gen_load_estimator = DefaultGeneratedLoadEstimator()

    def update(self, system):
        env = EnvironmentInput()

        env.attached_users = self.coverage.update(system, env)
        env.generated_load = self.gen_load_estimator.calc_all_loads(system, env)

        self.routing.update(system, env)
        env.net_delay = self.routing.get_all_paths_length()
        env.net_path = self.routing.get_all_paths()

        return env

    def stop(self):
        pass

