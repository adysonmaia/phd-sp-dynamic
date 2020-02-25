from abc import ABC, abstractmethod


class Coverage(ABC):
    def __init__(self, system=None):
        ABC.__init__(self)
        self.system = system

    @abstractmethod
    def update(self, time):
        pass

