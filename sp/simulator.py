from sp.model.system import System
from sp.coverage.min_dist import MinDistCoverage
from sp.routing.shortest_path import ShortestPathRouting


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

    def _init_sim(self):
        if self._scenario is None:
            raise ValueError("Scenario not defined")

        self._current_time = self._start_time
        self._system_state = System()
        self._system_state.scenario = self._scenario

        if self._coverage is None:
            self._coverage = MinDistCoverage()
        self._coverage.system = self._system_state

        if self._routing is None:
            self._routing = ShortestPathRouting()
        self._routing.system = self._system_state

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
        # TODO: implement this method
        self._update_mobility()
        self._update_coverage()
        self._update_request_load()

    def _update_mobility(self):
        for user in self._system_state.users:
            user.update_position(self._current_time)

    def _update_coverage(self):
        self._coverage.update(self._current_time)

    def _update_request_load(self):
        pass

    def _update_monitor(self):
        # TODO: implement this method
        pass

    def _update_controller(self):
        # TODO: implement this method
        return None

    def _apply_control_decision(self, decision):
        # TODO: implement this method
        pass
