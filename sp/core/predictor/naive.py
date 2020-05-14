from .predictor import Predictor


class NaivePredictor(Predictor):
    """Naive Forecasting Method.
    It simply sets all forecasts to be the value of the last observation

    See Also: https://otexts.com/fpp2/simple-methods.html
    """

    def __init__(self):
        """Initialization
        """
        Predictor.__init__(self)
        self._last_value = None

    def clear(self):
        """Clear forecasting information
        """
        self._last_value = None

    def update(self, datum):
        """Update time series data

        Args:
            datum (Union[list, float]): new item (datum) in the data or the complete data
        """
        if isinstance(datum, list):
            self._last_value = datum[-1]
        else:
            self._last_value = datum

    def predict(self, steps=1):
        """Predict next values

        Args:
            steps (int): number of values to predict
        Returns:
            list: predicted data
        """
        return [self._last_value] * steps
