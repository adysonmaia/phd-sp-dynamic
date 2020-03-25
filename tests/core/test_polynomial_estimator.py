from sp.core.estimator.polynomial import PolynomialEstimator, LinearEstimator, ConstEstimator
import unittest


class PolyEstimatorTestCase(unittest.TestCase):
    def test_poly_estimator(self):
        f = PolynomialEstimator()  # f(x) = 0
        self.assertEqual(f(0.0), 0.0)
        self.assertEqual(f.calc(0.0), 0.0)
        self.assertEqual(f.calc(1.0), 0.0)
        self.assertEqual(f.calc(2.0), 0.0)
        self.assertEqual(f.calc(3.0), 0.0)

        f = PolynomialEstimator([])  # f(x) = 0
        self.assertEqual(f(0.0), 0.0)
        self.assertEqual(f.calc(0.0), 0.0)
        self.assertEqual(f.calc(1.0), 0.0)
        self.assertEqual(f.calc(2.0), 0.0)
        self.assertEqual(f.calc(3.0), 0.0)

        f = PolynomialEstimator([1.0])  # f(x) = 1
        self.assertEqual(f(0.0), 1.0)
        self.assertEqual(f.calc(0.0), 1.0)
        self.assertEqual(f.calc(1.0), 1.0)
        self.assertEqual(f.calc(2.0), 1.0)
        self.assertEqual(f.calc(3.0), 1.0)

        f = PolynomialEstimator([1.0, 1.0])  # f(x) = x + 1
        self.assertEqual(f(0.0), 1.0)
        self.assertEqual(f.calc(0.0), 1.0)
        self.assertEqual(f.calc(1.0), 2.0)
        self.assertEqual(f.calc(2.0), 3.0)
        self.assertEqual(f.calc(3.0), 4.0)

        f = PolynomialEstimator([1.0, 1.0, 1.0])  # f(x) = x^2 + x + 1
        self.assertEqual(f(0.0), 1.0)
        self.assertEqual(f.calc(0.0), 1.0)
        self.assertEqual(f.calc(1.0), 3.0)
        self.assertEqual(f.calc(2.0), 7.0)
        self.assertEqual(f.calc(3.0), 13.0)

    def test_linear_estimator(self):
        f = LinearEstimator([])  # f(x) = 0
        self.assertEqual(f(0.0), 0.0)
        self.assertEqual(f.calc(0.0), 0.0)
        self.assertEqual(f.calc(1.0), 0.0)
        self.assertEqual(f.calc(2.0), 0.0)
        self.assertEqual(f.calc(3.0), 0.0)

        f = LinearEstimator([1.0])  # f(x) = 1
        self.assertEqual(f(0.0), 1.0)
        self.assertEqual(f.calc(0.0), 1.0)
        self.assertEqual(f.calc(1.0), 1.0)
        self.assertEqual(f.calc(2.0), 1.0)
        self.assertEqual(f.calc(3.0), 1.0)

        f = LinearEstimator([1.0, 1.0]) # f(x) = x + 1
        self.assertEqual(f(0.0), 1.0)
        self.assertEqual(f.calc(0.0), 1.0)
        self.assertEqual(f.calc(1.0), 2.0)
        self.assertEqual(f.calc(2.0), 3.0)
        self.assertEqual(f.calc(3.0), 4.0)

        f = LinearEstimator({"a": 2.0, "b": 2.0})  # f(x) = 2x + 2
        self.assertEqual(f(0.0), 2.0)
        self.assertEqual(f.calc(0.0), 2.0)
        self.assertEqual(f.calc(1.0), 4.0)
        self.assertEqual(f.calc(2.0), 6.0)
        self.assertEqual(f.calc(3.0), 8.0)

    def test_const_estimator(self):
        f = ConstEstimator()  # f(x) = 0
        self.assertEqual(f(0.0), 0.0)
        self.assertEqual(f.calc(0.0), 0.0)
        self.assertEqual(f.calc(1.0), 0.0)
        self.assertEqual(f.calc(2.0), 0.0)
        self.assertEqual(f.calc(3.0), 0.0)

        f = ConstEstimator(1.0)  # f(x) = 1
        self.assertEqual(f(0.0), 1.0)
        self.assertEqual(f.calc(0.0), 1.0)
        self.assertEqual(f.calc(1.0), 1.0)
        self.assertEqual(f.calc(2.0), 1.0)
        self.assertEqual(f.calc(3.0), 1.0)


if __name__ == '__main__':
    unittest.main()
