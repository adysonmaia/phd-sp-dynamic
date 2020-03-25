from abc import ABC, abstractmethod
import logging


class _MonitorActionsEnum:
    SIM_STARTED = "on_sim_started"
    SIM_ENDED = "on_sim_ended"
    TIME_SLOT_STARTED = "on_time_slot_started"
    TIME_SLOT_ENDED = "on_time_slot_ended"
    ENV_CTRL_STARTED = "on_env_ctrl_started"
    ENV_CTRL_ENDED = "on_env_ctrl_ended"
    SYS_CTRL_STARTED = "on_sys_ctrl_started"
    SYS_CTRL_ENDED = "on_sys_ctrl_ended"


class Monitor(ABC):
    actions = _MonitorActionsEnum()

    def __init__(self):
        ABC.__init__(self)
        self.simulator = None

    def __call__(self, *args, **kwargs):
        self.update(*args, **kwargs)

        action = args[0]
        action_method = getattr(self, action, None)
        if callable(action_method):
            args = args[1:]
            action_method(*args, **kwargs)

    def start(self, simulator):
        self.simulator = simulator

    def update(self, action, sim_time, *args, **kwargs):
        pass


class DefaultMonitor(Monitor):
    def update(self, action, sim_time, *args, **kwargs):
        logging.debug("SIM %f - %s", sim_time, action)

