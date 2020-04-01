from .scheduler import Scheduler


class AlwaysScheduler(Scheduler):
    def init_params(self):
        pass

    def clear_params(self):
        pass

    def needs_update(self, system, environment_input):
        return True

    def update(self, system, environment_input):
        return system, environment_input
