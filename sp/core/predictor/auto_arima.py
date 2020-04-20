from .predictor import Predictor
import pmdarima as pm
import warnings
import math


DEFAULT_ARIMA_PARAMS = {"suppress_warnings": True, 'error_action': 'ignore', 'stepwise': True}
DEFAULT_PREDICT_PARAMS = {}
DEFAULT_MAX_DATA_SIZE = math.inf

FIT_MIN_DATA_SIZE = 2


class AutoARIMAPredictor(Predictor):
    def __init__(self, max_data_size=DEFAULT_MAX_DATA_SIZE,
                 arima_params=None, predict_params=None):
        Predictor.__init__(self)
        self.max_data_size = max_data_size
        self.arima_params = arima_params
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
                    model_params.update(DEFAULT_ARIMA_PARAMS)
                    if self.arima_params is not None:
                        model_params.update(self.arima_params)
                    fit_results = pm.auto_arima(self._data, **model_params)
            except:
                pass

        self._fit_results = fit_results

    def predict(self, steps=1):
        prediction = None
        if self._fit_results is not None:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=Warning)

                    predict_params = {}
                    predict_params.update(DEFAULT_PREDICT_PARAMS)
                    if self.predict_params is not None:
                        predict_params.update(self.predict_params)
                    prediction = self._fit_results.predict(steps, **predict_params)
            except:
                pass

        if prediction is None:
            prediction = [self._data[-1]] * steps
        return prediction
