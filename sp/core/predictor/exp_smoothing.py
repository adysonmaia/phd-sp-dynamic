from .predictor import Predictor
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings

DEFAULT_MAX_DATA_SIZE = 10000
DEFAULT_ES_PARAMS = {}
DEFAULT_FIT_PARAMS = {}
DEFAULT_PREDICT_PARAMS = {}

FIT_MIN_DATA_SIZE = 2


class ExpSmoothingPredictor(Predictor):
    def __init__(self, max_data_size=DEFAULT_MAX_DATA_SIZE,
                 es_params=None, fit_params=None, predict_params=None):
        Predictor.__init__(self)
        self.max_data_size = max_data_size
        self.es_params = es_params
        self.fit_params = fit_params
        self.predict_params = predict_params

        self._data = []
        self._fit_results = None

    def clear(self):
        self._data.clear()
        self._fit_results = None

    def update(self, datum):
        self._data.append(datum)
        if len(self._data) > self.max_data_size:
            self._data.pop(0)

        fit_results = None
        if len(self._data) >= FIT_MIN_DATA_SIZE:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=Warning)

                    model_params = {}
                    model_params.update(DEFAULT_ES_PARAMS)
                    if self.es_params is not None:
                        model_params.update(self.es_params)
                    model = ExponentialSmoothing(self._data, **model_params)

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
