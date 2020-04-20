from sp.core.predictor import ARIMAPredictor, AutoARIMAPredictor, ExpSmoothingPredictor
import random
import unittest


class PredictorTestCase(unittest.TestCase):
    def test_arima(self):
        predictor = ARIMAPredictor()
        data_size = 100
        data = []
        for x in range(data_size):
            value = x + random.random()
            data.append(value)
            predictor.update(value)

        steps = 10
        prediction = predictor.predict(steps)
        self.assertEqual(len(prediction), steps)
        for value in prediction:
            self.assertLessEqual(value, data_size + steps)
            self.assertGreaterEqual(value, 0.0)

        predictor.update(data)
        prediction_2 = predictor.predict(steps)
        self.assertListEqual(list(prediction), list(prediction_2))

    def test_auto_arima(self):
        predictor = AutoARIMAPredictor()
        data_size = 10
        data = []
        for x in range(data_size):
            value = x + random.random()
            data.append(value)
            predictor.update(value)

        steps = 10
        prediction = predictor.predict(steps)
        self.assertEqual(len(prediction), steps)
        for value in prediction:
            self.assertLessEqual(value, data_size + steps)
            self.assertGreaterEqual(value, 0.0)

        predictor.update(data)
        prediction_2 = predictor.predict(steps)
        self.assertListEqual(list(prediction), list(prediction_2))

    def test_exp_smoothing(self):
        predictor = ExpSmoothingPredictor()
        data_size = 100
        data = []
        for x in range(data_size):
            value = x + random.random()
            data.append(value)
            predictor.update(value)

        steps = 10
        prediction = predictor.predict(steps)
        self.assertEqual(len(prediction), steps)
        first_value = prediction[0]
        for value in prediction:
            self.assertLessEqual(value, data_size + steps)
            self.assertGreaterEqual(value, 0.0)
            self.assertEqual(value, first_value)

        predictor.update(data)
        prediction_2 = predictor.predict(steps)
        self.assertListEqual(list(prediction), list(prediction_2))


if __name__ == '__main__':
    unittest.main()
