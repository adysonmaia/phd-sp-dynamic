from abc import ABC, abstractmethod


class Predictor(ABC):
    """Forecasting Abstract Class
    """

    @abstractmethod
    def update(self, *args, **kwargs):
        """Update time series data

        Args:
            *args: args
            **kwargs: kwargs
        """
        pass

    @abstractmethod
    def predict(self, steps=1):
        """Predict next values

        Args:
            steps (int): number of values to predict in the time series
        Returns:
            list: predicted data
        """
        pass

    @abstractmethod
    def clear(self):
        """Clear forecasting information
        """
        pass
