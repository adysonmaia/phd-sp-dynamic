from abc import ABC, abstractmethod


class Estimator(ABC):
    def __call__(self, *args, **kwargs):
        return self.calc(*args, **kwargs)

    @abstractmethod
    def calc(self, *args, **kwargs):
        pass

