from abc import ABC
import logging


class MonitorEventsEnum:
    """Simulation Events Enumeration
    """

    SIM_STARTED = "on_sim_started"
    """Simulation started"""

    SIM_ENDED = "on_sim_ended"
    """Simulation ended"""

    TIME_SLOT_STARTED = "on_time_slot_started"
    """A new time-slot started"""

    TIME_SLOT_ENDED = "on_time_slot_ended"
    """""The current time-slot ended"""

    ENV_CTRL_STARTED = "on_env_ctrl_started"
    """Environment controller started at the current time-slot"""

    ENV_CTRL_ENDED = "on_env_ctrl_ended"
    """Environment controller ended at the current time-slot"""

    SYS_CTRL_STARTED = "on_sys_ctrl_started"
    """System controller started at the current time-slot"""

    SYS_CTRL_ENDED = "on_sys_ctrl_ended"
    """System controller ended at the current time-slot"""


class Monitor(ABC):
    """Monitor events of a simulation.

    See :py:class:`MonitorEventEnum` to view the list of events

    There are two ways to catch an event.
    An inherited class can implement the method :py:meth:`Monitor.update` to catch all events.
    It is also possible to catch a specific event by implementing a method with the same name of the event.

    E.g.:

    .. code-block:: python

        class MyMonitor(Monitor):

            # Called when the simulation started
            def on_sim_started(self, sim_time, *args, **kwargs):
                pass

            # Called when the system controller started at a time-slot
            def on_sys_ctrl_started(self, sim_time, *args, **kwargs):
                pass

            # Called when the system controller ended at a time-slot
            def on_sys_ctrl_ended(self, sim_time, *args, **kwargs):
                pass

            # Called when the simulation ended
            def on_sim_ended(self, sim_time, *args, **kwargs):
                pass

            # Called for every event
            def update(self, event, sim_time, *args, **kwargs):
                pass

    """

    events = MonitorEventsEnum()
    """Enumeration of possible simulation events"""

    def __init__(self):
        """Initialization
        """
        ABC.__init__(self)
        self.simulator = None

    def __call__(self, *args, **kwargs):
        """Method is called when an event happens

        Args:
            *args: args
            **kwargs: kwargs
        """
        self.update(*args, **kwargs)

        action = args[0]
        action_method = getattr(self, action, None)
        if callable(action_method):
            args = args[1:]
            action_method(*args, **kwargs)

    def start(self, simulator):
        """Start the monitoring

        Args:
            simulator (sp.simulator.simulator.Simulator): simulator
        """
        self.simulator = simulator

    def update(self, event, sim_time, *args, **kwargs):
        """Method is called when an event happens

        Args:
            event (str): event name
            sim_time (float): simulation time when the event happened
            *args: args
            **kwargs: kwargs
        """
        pass


class DefaultMonitor(Monitor):
    """Default Monitor

    It logs all events as debug information
    """

    def update(self, event, sim_time, *args, **kwargs):
        """Method is called when an event happens

        Args:
            event (str): event name
            sim_time (float): simulation time when the event happened
            *args: args
            **kwargs: kwargs
        """
        logging.debug("SIM %f - %s", sim_time, event)

