from sp.core.time_series import TimeSeries, InterpolatedTimeSeries, ConstantTimeSeries
import unittest


class TimeSeriesTestCase(unittest.TestCase):
    def test_time_series(self):
        ts = TimeSeries()

        nb_items = 100
        for time in range(nb_items):
            value = time + 1
            ts.set_value(time, value)

        self.assertEqual(len(ts.items), nb_items)
        for time in range(nb_items):
            value = time + 1
            self.assertEqual(ts.get_value(time), value)
            self.assertEqual(ts[time], value)

        for (time, ts_value) in ts:
            value = time + 1
            self.assertEqual(ts_value, value)

        time_list = []
        for (time, ts_value) in ts.items:
            value = time + 1
            time_list.append(time)
            self.assertEqual(ts_value, value)

        time_list_len = len(time_list)
        self.assertEqual(time_list_len, nb_items)
        for i in range(time_list_len):
            prev_i = int(max(0, i - 1))
            next_i = int(min(i + 1, time_list_len - 1))

            time = time_list[i]
            prev_time = time_list[prev_i]
            next_time = time_list[next_i]
            self.assertLessEqual(time, next_time)
            self.assertGreaterEqual(time, prev_time)

    def test_const_ts(self):
        value = 5.0
        ts = ConstantTimeSeries(value=value)

        self.assertEqual(ts.get_value(), value)
        for time in range(10):
            self.assertEqual(ts.get_value(time), value)
            self.assertEqual(ts[time], value)

    def test_interpolated_ts(self):
        ts = InterpolatedTimeSeries()

        time_start = 1
        time_end = 9
        time_step = 2
        for time in range(time_start, time_end + 1, time_step):
            value = time
            ts.set_value(time, value)

        for time in range(time_start, time_end + 1, time_step):
            value = time
            self.assertEqual(ts.get_value(time), value)

        inter_time_start = time_start + 1
        inter_time_end = time_end - 1
        inter_time_step = time_step
        for time in range(inter_time_start, inter_time_end + 1, inter_time_step):
            value = time
            self.assertEqual(ts.get_value(time), value)

        self.assertRaises(KeyError, ts.get_value, time_start - 1)

        self.assertEqual(ts.get_value(time_start - 1, time_tolerance=time_step), time_start)
        self.assertEqual(ts.get_value(time_end + 1, time_tolerance=time_step), time_end)
