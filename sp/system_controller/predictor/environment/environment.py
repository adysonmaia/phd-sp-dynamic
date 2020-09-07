from sp.core.predictor import Predictor
from sp.core.model import System, EnvironmentInput
from abc import abstractmethod


class EnvironmentPredictor(Predictor):
    """Environment Predictor Abstract Class

    It forecasting next environment inputs
    """

    @abstractmethod
    def init_params(self):
        """Initialize parameters for the simulation
        """
        pass

    @abstractmethod
    def update(self, system, environment_input):
        """Update predictor at a simulation time with a system's state and environment input

        Args:
            system (System): system's state
            environment_input (EnvironmentInput): environment input
        """
        pass

    @abstractmethod
    def predict(self, steps=1):
        """Predict next environment inputs

        Args:
            steps (int): number of values to predict
        Returns:
            list(EnvironmentInput): predicted data
        """
        pass

    @abstractmethod
    def clear(self):
        """Clear forecasting information
        """
        pass



