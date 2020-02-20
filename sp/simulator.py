from sp.model.system import System


class Simulator:
    def __init__(self):
        self._start_time = 0
        self._stop_time = 0
        self._step_time = 1
        self._monitor = None
        self._controller = None
        self._scenario = None
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

    def run(self):
        self._current_time = self._start_time
        self._system_state = System()
        self._system_state.scenario = self._scenario

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

    def _update_mobility(self):
        for user in self._system_state.users:
            user.update_position(self._current_time)

    def _update_monitor(self):
        # TODO: implement this method
        pass

    def _update_controller(self):
        # TODO: implement this method
        return None

    def _apply_control_decision(self, decision):
        # TODO: implement this method
        pass
