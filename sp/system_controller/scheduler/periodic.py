from sp.core.model import EnvironmentInput, System
from . import Scheduler
from statistics import mean
import copy


class PeriodicScheduler(Scheduler):
    def __init__(self, period=1):
        Scheduler.__init__(self)
        self.period = period
        self._last_update = None
        self._env_inputs = None
        self._update_count = -1

    def start(self):
        self._last_update = None
        self._update_count = 0
        self._env_inputs = []

    def needs_update(self, system, environment_input):
        self._env_inputs.append(copy.copy(environment_input))

        return self._last_update is None or system.time - self._last_update >= self.period

    def update(self, system, environment_input):
        slotted_system = self._get_slotted_system(system, environment_input)
        slotted_env_input = self._get_slotted_environment_input(system, environment_input)

        self._last_update = system.time
        self._env_inputs.clear()
        self._update_count += 1

        return slotted_system, slotted_env_input

    def stop(self):
        pass

    def _get_slotted_system(self, system, environment_input):
        slotted_system = copy.copy(system)
        slotted_system.time = self._update_count
        slotted_system.sampling_time = self.period

        return slotted_system

    def _get_slotted_environment_input(self, system, environment_input):
        if len(self._env_inputs) < 1:
            return environment_input

        # TODO: it is really necessary to do this ?
        slotted_env = EnvironmentInput.create_empty(system)
        for app in system.apps:
            for src_node in system.nodes:
                values = [env.get_generated_load(app.id, src_node.id) for env in self._env_inputs]
                slotted_env.generated_load[app.id][src_node.id] = mean(values)

                for dst_node in system.nodes:
                    values = [env.get_net_delay(app.id, src_node.id, dst_node.id) for env in self._env_inputs]
                    slotted_env.net_delay[app.id][src_node.id][dst_node.id] = mean(values)

        return slotted_env
