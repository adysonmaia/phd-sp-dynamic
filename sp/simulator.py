from sp.model.system import System
from sp.coverage.min_dist import MinDistCoverage
from sp.routing.shortest_path import ShortestPathRouting
from sp.estimator.link_delay import DefaultLinkDelayEstimator
from sp.estimator.request_load import DefaultRequestLoadEstimator
from sp.estimator.queue_size import DefaultQueueSizeEstimator


class Simulator:
    def __init__(self):
        self._start_time = 0
        self._stop_time = 0
        self._step_time = 1
        self._scenario = None

        self._monitor = None
        self._controller = None
        self._routing = None
        self._coverage = None

        self._link_delay_estimator = None
        self._req_load_estimator = None
        self._queue_size_estimator = None

        self._system_state = None
        self._current_time = 0

    def set_time(self, stop, start=0, step=1):
        self._start_time = start
        self._stop_time = stop
        self._step_time = step
        return self

    def set_scenario(self, scenario):
        self._scenario = scenario
        return self

    def set_monitor(self, monitor):
        self._monitor = monitor
        return self

    def set_controller(self, controller):
        self._controller = controller
        return self

    def set_routing(self, routing):
        self._routing = routing
        return self

    def set_coverage(self, coverage):
        self._coverage = coverage
        return self

    def set_request_load_estimator(self, estimator):
        self._req_load_estimator = estimator
        return self

    def set_link_delay_estimator(self, estimator):
        self._link_delay_estimator = estimator
        return self

    def _init_sim(self):
        if self._scenario is None:
            raise ValueError("Scenario not defined")

        self._current_time = self._start_time
        self._system_state = System()
        self._system_state.scenario = self._scenario

        if self._coverage is None:
            self._coverage = MinDistCoverage()
        self._coverage.system = self._system_state

        if self._link_delay_estimator is None:
            self._link_delay_estimator = DefaultLinkDelayEstimator()
        self._link_delay_estimator.system = self._system_state

        if self._routing is None:
            self._routing = ShortestPathRouting()
            self._routing.estimator = self._link_delay_estimator
            self._routing.static_routing = True
        self._routing.system = self._system_state

        if self._req_load_estimator is None:
            self._req_load_estimator = DefaultRequestLoadEstimator()
        self._req_load_estimator.system = self._system_state

        if self._queue_size_estimator is None:
            self._queue_size_estimator = DefaultQueueSizeEstimator()
        self._queue_size_estimator.system = self._system_state

    def run(self):
        self._init_sim()

        while self._current_time < self._stop_time:
            self._system_state.time = self._current_time
            self._update_system()
            self._update_monitor()
            decision = self._update_controller()
            if decision is not None:
                self._apply_control_decision(decision)
                self._update_monitor()
            self._current_time += self._step_time

    def _update_system(self):
        self._update_mobility()
        self._update_coverage()
        self._update_request_load()
        self._update_routing()

    def _update_mobility(self):
        for user in self._system_state.users:
            user.update_position(self._current_time)

    def _update_coverage(self):
        self._coverage.update(self._current_time)

    def _update_request_load(self):
        self._system_state.request_load = self._req_load_estimator.calc_all_loads()

    def _update_app_queue_size(self):
        self._system_state.app_queue_size = self._queue_size_estimator.calc_all_queue_sizes()

    def _update_routing(self):
        self._routing.update(self._current_time)
        self._system_state.net_delay = self._routing.get_all_paths_length()
        self._system_state.net_path = self._routing.get_all_paths()

    def _update_monitor(self):
        # TODO: implement this method
        pass

    def _update_controller(self):
        # TODO: implement this method
        return None

    def _apply_control_decision(self, decision):
        # TODO: implement this method
        pass
