from sp.estimator.polynomial import PolyFunc, LinearFunc, ConstFunc
import unittest


class PolyFuncTestCase(unittest.TestCase):
    def test_poly_func(self):
        f = PolyFunc()  # f(x) = 0
        self.assertEqual(f.calc(0.0), 0.0)
        self.assertEqual(f.calc(1.0), 0.0)
        self.assertEqual(f.calc(2.0), 0.0)
        self.assertEqual(f.calc(3.0), 0.0)

        f = PolyFunc([])  # f(x) = 0
        self.assertEqual(f.calc(0.0), 0.0)
        self.assertEqual(f.calc(1.0), 0.0)
        self.assertEqual(f.calc(2.0), 0.0)
        self.assertEqual(f.calc(3.0), 0.0)

        f = PolyFunc([1.0])  # f(x) = 1
        self.assertEqual(f.calc(0.0), 1.0)
        self.assertEqual(f.calc(1.0), 1.0)
        self.assertEqual(f.calc(2.0), 1.0)
        self.assertEqual(f.calc(3.0), 1.0)

        f = PolyFunc([1.0, 1.0])  # f(x) = x + 1
        self.assertEqual(f.calc(0.0), 1.0)
        self.assertEqual(f.calc(1.0), 2.0)
        self.assertEqual(f.calc(2.0), 3.0)
        self.assertEqual(f.calc(3.0), 4.0)

        f = PolyFunc([1.0, 1.0, 1.0]) # f(x) = x^2 + x + 1
        self.assertEqual(f.calc(0.0), 1.0)
        self.assertEqual(f.calc(1.0), 3.0)
        self.assertEqual(f.calc(2.0), 7.0)
        self.assertEqual(f.calc(3.0), 13.0)

    def test_linear_func(self):
        f = LinearFunc([])  # f(x) = 0
        self.assertEqual(f.calc(0.0), 0.0)
        self.assertEqual(f.calc(1.0), 0.0)
        self.assertEqual(f.calc(2.0), 0.0)
        self.assertEqual(f.calc(3.0), 0.0)

        f = LinearFunc([1.0])  # f(x) = 1
        self.assertEqual(f.calc(0.0), 1.0)
        self.assertEqual(f.calc(1.0), 1.0)
        self.assertEqual(f.calc(2.0), 1.0)
        self.assertEqual(f.calc(3.0), 1.0)

        f = LinearFunc([1.0, 1.0]) # f(x) = x + 1
        self.assertEqual(f.calc(0.0), 1.0)
        self.assertEqual(f.calc(1.0), 2.0)
        self.assertEqual(f.calc(2.0), 3.0)
        self.assertEqual(f.calc(3.0), 4.0)

        f = LinearFunc({"a": 2.0, "b": 2.0})  # f(x) = 2x + 2
        self.assertEqual(f.calc(0.0), 2.0)
        self.assertEqual(f.calc(1.0), 4.0)
        self.assertEqual(f.calc(2.0), 6.0)
        self.assertEqual(f.calc(3.0), 8.0)

    def test_const_func(self):
        f = ConstFunc()  # f(x) = 0
        self.assertEqual(f.calc(0.0), 0.0)
        self.assertEqual(f.calc(1.0), 0.0)
        self.assertEqual(f.calc(2.0), 0.0)
        self.assertEqual(f.calc(3.0), 0.0)

        f = ConstFunc(1.0)  # f(x) = 1
        self.assertEqual(f.calc(0.0), 1.0)
        self.assertEqual(f.calc(1.0), 1.0)
        self.assertEqual(f.calc(2.0), 1.0)
        self.assertEqual(f.calc(3.0), 1.0)


if __name__ == '__main__':
    unittest.main()
