from . import Scheduler


class PeriodicScheduler(Scheduler):
    def __init__(self, period=1):
        Scheduler.__init__(self)
        self.period = period
        self._last_update = None

    def start(self):
        self._last_update = None

    def needs_update(self, system):
        return self._last_update is None or system.time - self._last_update >= self.period

    def update(self, system):
        self._last_update = system.time

    def stop(self):
        pass
