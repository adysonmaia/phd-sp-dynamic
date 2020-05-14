from sp.core.predictor import Predictor
from abc import abstractmethod


class EnvironmentPredictor(Predictor):
    @abstractmethod
    def update(self, system, environment_input):
        pass

    @abstractmethod
    def predict(self, steps=1):
        pass

    @abstractmethod
    def clear(self):
        pass



