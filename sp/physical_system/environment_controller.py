from sp.physical_system.coverage.min_distance import MinDistanceCoverage
from sp.physical_system.routing.shortest_path import ShortestPathRouting
from sp.physical_system.estimator import DefaultLinkDelayEstimator, DefaultGeneratedLoadEstimator
from sp.core.model import EnvironmentInput


class EnvironmentController:
    def __init__(self):
        self.routing = ShortestPathRouting()
        self.coverage = MinDistanceCoverage()
        self.link_delay_estimator = DefaultLinkDelayEstimator()
        self.gen_load_estimator = DefaultGeneratedLoadEstimator()

    def init_params(self):
        if self.routing is None:
            self.routing.link_delay_estimator = self.link_delay_estimator
            self.routing.static_routing = True

    def clear_params(self):
        pass

    def update(self, system):
        env = EnvironmentInput()

        time_tol = system.sampling_time
        env.attached_users = self.coverage.update(system, env, time_tolerance=time_tol)
        env.generated_load = self.gen_load_estimator.calc_all_loads(system, env, time_tolerance=time_tol)

        self.routing.update(system, env)
        env.net_delay = self.routing.get_all_paths_length()
        env.net_path = self.routing.get_all_paths()

        return env
