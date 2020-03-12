from abc import ABC, abstractmethod


class Scheduler(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def needs_update(self, system, environment_input):
        pass

    @abstractmethod
    def update(self, system, environment_input):
        pass

    @abstractmethod
    def stop(self):
        pass
