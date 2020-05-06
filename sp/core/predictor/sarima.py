from .predictor import Predictor
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima_model import ARIMA
import warnings
import math


DEFAULT_SARIMA_PARAMS = {"order": (1, 1, 1)}
DEFAULT_FIT_PARAMS = {"disp": False}
DEFAULT_PREDICT_PARAMS = {"typ": "levels"}
DEFAULT_MAX_DATA_SIZE = math.inf

FIT_MIN_DATA_SIZE = 2


class SARIMAPredictor(Predictor):
    def __init__(self, max_data_size=DEFAULT_MAX_DATA_SIZE,
                 sarima_params=None, fit_params=None, predict_params=None):
        Predictor.__init__(self)
        self.max_data_size = max_data_size
        self.sarima_params = sarima_params
        self.fit_params = fit_params
        self.predict_params = predict_params

        self._data = []
        self._fit_results = None

    def clear(self):
        self._data.clear()
        self._fit_results = None

    def update(self, datum):
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
                    model_params.update(DEFAULT_SARIMA_PARAMS)
                    if self.sarima_params is not None:
                        model_params.update(self.sarima_params)

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
