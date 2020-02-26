from abc import ABC, abstractmethod


class Controller(ABC):
    def __init__(self):
        ABC.__init__(self)
        self.system = None

    def init_params(self, system):
        self.system = system
        if self.system is None:
            raise ValueError("System not defined")

    @abstractmethod
    def update(self, system):
        pass
