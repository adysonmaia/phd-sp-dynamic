from .predictor import Predictor
import pmdarima as pm
import warnings
import math


DEFAULT_INIT_PARAMS = {"suppress_warnings": True, 'error_action': 'ignore', 'stepwise': True}
DEFAULT_PREDICT_PARAMS = {}
DEFAULT_MAX_DATA_SIZE = math.inf

FIT_MIN_DATA_SIZE = 2


class AutoARIMAPredictor(Predictor):
    """Auto ARIMA Forecasting Method

    It automatically discovers the optimal order for an ARIMA model

    See Also: https://alkaline-ml.com/pmdarima/index.html

    Attributes:
        max_data_size (int): maximum data size
        predict_params (dict): parameters of predict method.
            See Also: https://alkaline-ml.com/pmdarima/modules/generated/pmdarima.arima.ARIMA.html#pmdarima.arima.ARIMA.predict
        init_params (dict): parameters of :py:func:`pm.auto_arima` function.
            See Also: https://alkaline-ml.com/pmdarima/modules/generated/pmdarima.arima.auto_arima.html#pmdarima.arima.auto_arima
    """

    def __init__(self, max_data_size=DEFAULT_MAX_DATA_SIZE, predict_params=None, **init_params):
        """

        Args:
            max_data_size (int): maximum data size
            predict_params (dict): parameters of predict method.
            **init_params: parameters of :py:func:`pm.auto_arima` function.
        """
        Predictor.__init__(self)
        self.max_data_size = max_data_size
        self.init_params = init_params
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
                    if "m" in model_params and model_params["m"] >= len(self._data):
                        del model_params["m"]
                        model_params["seasonal"] = False

                    fit_results = pm.auto_arima(self._data, **model_params)
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
