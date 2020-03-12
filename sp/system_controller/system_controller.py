from sp.system_controller.scheduler.periodic import PeriodicScheduler
from sp.system_controller.optimizer.static.cloud import CloudOptimizer
from sp.system_controller.optimizer import OptimizerError


class SystemController:
    def __init__(self):
        self.scheduler = None
        self.optimizer = None

    def start(self):
        if self.scheduler is None:
            self.scheduler = PeriodicScheduler()
        if self.optimizer is None:
            self.optimizer = CloudOptimizer()

        self.scheduler.start()

    def update(self, system, environment_input):
        control_input = None

        if self.scheduler.needs_update(system, environment_input):
            estimated_system, estimated_env_input = self.scheduler.update(system, environment_input)
            try:
                control_input = self.optimizer.solve(estimated_system, estimated_env_input)
            except OptimizerError:
                pass

        return control_input

    def stop(self):
        self.scheduler.stop()
