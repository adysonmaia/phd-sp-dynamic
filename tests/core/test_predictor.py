from sp.core.predictor.arima import ARIMAPredictor
from sp.core.predictor.exp_smoothing import ExpSmoothingPredictor
import random
import unittest


class PredictorTestCase(unittest.TestCase):
    def test_arima(self):
        predictor = ARIMAPredictor()
        data_size = 100
        for x in range(data_size):
            value = x + random.random()
            predictor.update(value)

        steps = 10
        prediction = predictor.predict(steps)
        self.assertEqual(len(prediction), steps)
        for value in prediction:
            self.assertLessEqual(value, data_size + steps)
            self.assertGreaterEqual(value, 0.0)

    def test_exp_smoothing(self):
        predictor = ExpSmoothingPredictor()
        data_size = 100
        for x in range(data_size):
            value = x + random.random()
            predictor.update(value)

            steps = 10
            prediction = predictor.predict(steps)
            self.assertEqual(len(prediction), steps)
            first_value = prediction[0]
            for value in prediction:
                self.assertLessEqual(value, data_size + steps)
                self.assertGreaterEqual(value, 0.0)
                self.assertEqual(value, first_value)


if __name__ == '__main__':
    unittest.main()
