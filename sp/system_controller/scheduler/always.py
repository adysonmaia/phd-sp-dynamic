from . import Scheduler


class AlwaysScheduler(Scheduler):
    def start(self):
        pass

    def needs_update(self, system, environment_input):
        return True

    def update(self, system, environment_input):
        return system, environment_input

    def stop(self):
        pass
