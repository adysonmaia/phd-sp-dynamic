from .predictor import Predictor
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima_model import ARIMA
import warnings
import math


DEFAULT_INIT_PARAMS = {"order": (1, 1, 1)}
DEFAULT_FIT_PARAMS = {"disp": False}
DEFAULT_PREDICT_PARAMS = {"typ": "levels"}
DEFAULT_MAX_DATA_SIZE = math.inf

FIT_MIN_DATA_SIZE = 2


class SARIMAPredictor(Predictor):
    """Seasonal AutoRegressive Integrated Moving Average (SARIMA) Forecasting Method

    See Also:

    * https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html#statsmodels.tsa.statespace.sarimax.SARIMAX
    * https://otexts.com/fpp2/seasonal-arima.html
    """

    def __init__(self, max_data_size=DEFAULT_MAX_DATA_SIZE, fit_params=None, predict_params=None, **kwargs):
        """Initialization

        Args:
            max_data_size (int): maximum data size
            fit_params (dict): parameters of fit method.
                See Also: https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.fit.html#statsmodels.tsa.statespace.sarimax.SARIMAX.fit
            predict_params (dict): parameters of predict method.
                See Also: https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.mlemodel.MLEResults.predict.html#statsmodels.tsa.statespace.mlemodel.MLEResults.predict
            **kwargs: initialization parameters of :py:class:`SARIMAX` class.
                See Also: https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html#statsmodels.tsa.statespace.sarimax.SARIMAX
        """
        Predictor.__init__(self)
        self.max_data_size = max_data_size
        self.init_params = kwargs
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

                    model_params = {}
                    model_params.update(DEFAULT_INIT_PARAMS)
                    if self.init_params:
                        model_params.update(self.init_params)

                    seasonal_period = None
                    if 'seasonal_order' in model_params and len(model_params['seasonal_order']) >= 4:
                        seasonal_period = model_params['seasonal_order'][3]

                    model_class = SARIMAX
                    if seasonal_period is None or len(self._data) <= seasonal_period:
                        model_class = ARIMA
                        if 'seasonal_order' in model_params:
                            del model_params['seasonal_order']

                    model = model_class(self._data, **model_params)

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
