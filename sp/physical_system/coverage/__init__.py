from abc import ABC, abstractmethod


class Coverage(ABC):
    @abstractmethod
    def update(self, system, environment, time_tolerance=None, distance_tolerance=None):
        pass

