from sp.core.estimator.load import TimeSeriesLoadEstimator, ConstantLoadEstimator, from_json
from sp.core.time_series import TimeSeries
import unittest


class LoadEstimatorTestCase(unittest.TestCase):
    def test_constant_estimator(self):
        load = 10.0
        estimator = ConstantLoadEstimator(load=load)
        self.assertEqual(estimator.load, load)
        self.assertEqual(estimator.calc(), load)
        self.assertEqual(estimator(), load)

        nb_times = 20
        for time in range(nb_times):
            self.assertEqual(estimator(time), load)

    def test_ts_estimator(self):
        estimator = TimeSeriesLoadEstimator()
        ts = TimeSeries()
        series_len = 10
        for time in range(series_len):
            load = time + 1.0
            ts.set_value(time, load)
        estimator.series = ts

        for time in range(series_len):
            self.assertEqual(estimator(time), ts[time])
        for time in range(series_len, 2 * series_len):
            self.assertEqual(estimator(time), 0.0)

    def test_from_json(self):
        const_load = 10.0
        json_data = const_load
        estimator = from_json(json_data)
        self.assertIsInstance(estimator, ConstantLoadEstimator)
        self.assertEqual(estimator(), const_load)

        series_len = 10
        json_data = [{'t': time, 'v': time + 1.0} for time in range(series_len)]
        estimator = from_json(json_data)
        self.assertIsInstance(estimator, TimeSeriesLoadEstimator)
        self.assertIsInstance(estimator.series, TimeSeries)
        self.assertEqual(len(estimator.series.items), series_len)
        for item in json_data:
            time = item['t']
            load = item['v']
            self.assertEqual(estimator(time), load)

        series_len = 10
        json_data = [[time + 1.0, time] for time in range(series_len)]
        estimator = from_json(json_data)
        self.assertIsInstance(estimator, TimeSeriesLoadEstimator)
        self.assertIsInstance(estimator.series, TimeSeries)
        self.assertEqual(len(estimator.series.items), series_len)
        for item in json_data:
            load = item[0]
            time = item[1]
            self.assertEqual(estimator(time), load)
