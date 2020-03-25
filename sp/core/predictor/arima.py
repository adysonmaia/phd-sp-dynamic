from .predictor import Predictor
from statsmodels.tsa.arima_model import ARIMA
import warnings


DEFAULT_ARIMA_PARAMS = {"order": (1, 1, 1)}
DEFAULT_FIT_PARAMS = {"disp": False}
DEFAULT_PREDICT_PARAMS = {"typ": "levels"}
DEFAULT_MAX_DATA_SIZE = 10000

FIT_MIN_DATA_SIZE = 2


class ARIMAPredictor(Predictor):
    def __init__(self, max_data_size=DEFAULT_MAX_DATA_SIZE,
                 arima_params=None, fit_params=None, predict_params=None):
        Predictor.__init__(self)
        self._data = []
        self._fit_results = None
        self._max_data_size = max_data_size

        self._arima_params = arima_params
        self._fit_params = fit_params
        self._predict_params = predict_params

    def update(self, datum):
        self._data.append(datum)
        if len(self._data) > self._max_data_size:
            self._data.pop(0)

        fit_results = None
        if len(self._data) >= FIT_MIN_DATA_SIZE:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=Warning)

                    model_params = self._arima_params if self._arima_params else DEFAULT_ARIMA_PARAMS
                    model = ARIMA(self._data, **model_params)

                    fit_params = self._fit_params if self._fit_params else DEFAULT_FIT_PARAMS
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

                    predict_params = self._predict_params if self._predict_params else DEFAULT_PREDICT_PARAMS
                    prediction = self._fit_results.predict(start, end, **predict_params)
            except:
                pass

        if prediction is None:
            prediction = [self._data[-1]] * steps
        return prediction
