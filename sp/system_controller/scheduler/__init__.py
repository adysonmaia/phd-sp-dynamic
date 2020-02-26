from abc import ABC, abstractmethod


class Scheduler(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def needs_update(self, system):
        pass

    @abstractmethod
    def update(self, system):
        pass

    @abstractmethod
    def stop(self):
        pass
