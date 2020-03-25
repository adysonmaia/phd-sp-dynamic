from abc import ABC, abstractmethod


class Predictor(ABC):
    @abstractmethod
    def update(self, *args, **kwargs):
        pass

    @abstractmethod
    def predict(self, steps=1):
        pass
