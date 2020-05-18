from .predictor import Predictor
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
import warnings
import math


DEFAULT_MAX_DATA_SIZE = math.inf
DEFAULT_FIT_PARAMS = {}
DEFAULT_PREDICT_PARAMS = {}

FIT_MIN_DATA_SIZE = 2


class SimpleExpSmoothingPredictor(Predictor):
    """Simple Exponential Smoothing Forecasting Method

    See Also:

    * https://www.statsmodels.org/stable/generated/statsmodels.tsa.holtwinters.SimpleExpSmoothing.html#statsmodels.tsa.holtwinters.SimpleExpSmoothing
    * https://otexts.com/fpp2/expsmooth.html

    Attributes:
        max_data_size (int): maximum data size
        predict_params (dict): parameters of predict method.
            See Also: https://www.statsmodels.org/stable/generated/statsmodels.tsa.holtwinters.HoltWintersResults.predict.html#statsmodels.tsa.holtwinters.HoltWintersResults.predict
        fit_params (dict): fit parameters of :py:class:`SimpleExpSmoothing` class.
            See Also: https://www.statsmodels.org/stable/generated/statsmodels.tsa.holtwinters.SimpleExpSmoothing.fit.html#statsmodels.tsa.holtwinters.SimpleExpSmoothing.fit
    """

    def __init__(self, max_data_size=DEFAULT_MAX_DATA_SIZE, predict_params=None, **fit_params):
        """Initialization

        Args:
            max_data_size (int): maximum data size
            predict_params (dict): parameters of predict method.
            **fit_params: fit parameters of :py:class:`SimpleExpSmoothing` class.
        """
        Predictor.__init__(self)
        self.max_data_size = max_data_size
        self.fit_params = fit_params
        self.predict_params = predict_params

        self._data = []
        self._fit_results = None

    def clear(self):
        """Clear forecasting information
        """
        self._data.clear()
        self._fit_results = None

    def update(self, datum):
        """Update time series data

        Args:
            datum (Union[list, float]): new item (datum) in the data or the complete data
        """
        if isinstance(datum, list):
            self._data = datum
        else:
            self._data.append(datum)

        if len(self._data) > self.max_data_size:
            pos = int(len(self._data) - self.max_data_size)
            self._data = self._data[pos:]

        fit_results = None
        if len(self._data) >= FIT_MIN_DATA_SIZE:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=Warning)

                    model = SimpleExpSmoothing(self._data)

                    fit_params = {}
                    fit_params.update(DEFAULT_FIT_PARAMS)
                    if self.fit_params is not None:
                        fit_params.update(self.fit_params)
                    fit_results = model.fit(**fit_params)
            except:
                pass

        self._fit_results = fit_results

    def predict(self, steps=1):
        """Predict next values

        Args:
            steps (int): number of values to predict
        Returns:
            list: predicted data
        """
        prediction = None
        if self._fit_results is not None:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=Warning)

                    start = len(self._data)
                    end = start + steps - 1

                    predict_params = {}
                    predict_params.update(DEFAULT_PREDICT_PARAMS)
                    if self.predict_params is not None:
                        predict_params.update(self.predict_params)
                    prediction = self._fit_results.predict(start, end, **predict_params)
            except:
                pass

        if prediction is None:
            prediction = [self._data[-1]] * steps
        return prediction
