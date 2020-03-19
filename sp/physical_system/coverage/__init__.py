from abc import ABC, abstractmethod


class Coverage(ABC):
    @abstractmethod
    def update(self, system, environment):
        pass

