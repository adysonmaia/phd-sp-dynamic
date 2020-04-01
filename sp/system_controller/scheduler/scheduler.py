from abc import ABC, abstractmethod


class Scheduler(ABC):
    @abstractmethod
    def init_params(self):
        pass

    @abstractmethod
    def clear_params(self):
        pass

    @abstractmethod
    def needs_update(self, system, environment_input):
        pass

    @abstractmethod
    def update(self, system, environment_input):
        pass
