from sp.position.cartesian import CartesianPosition
from sp.position.gps import GpsPosition
import unittest


class PositionTestCase(unittest.TestCase):
    def test_cartesian_creation(self):
        values = [10.5, 50.1]
        p = CartesianPosition(values)
        self.assertListEqual(list(p.values), values)
        self.assertEqual(p[0], values[0])
        self.assertEqual(p[1], values[1])
        self.assertEqual(p.x, values[0])
        self.assertEqual(p.y, values[1])

        p = CartesianPosition(*values)
        self.assertListEqual(list(p.values), values)

        p = CartesianPosition()
        p.values = values
        self.assertListEqual(list(p.values), values)

        p = CartesianPosition()
        p[0] = 1.5
        p[1] = 2.0
        self.assertEqual(p.x, 1.5)
        self.assertEqual(p.y, 2.0)
        p.x = 3.141
        p.y = 2.718
        self.assertEqual(p[0], 3.141)
        self.assertEqual(p[1], 2.718)

        p.z = 1.618
        self.assertEqual(p[2], 1.618)
        self.assertEqual(p.z, 1.618)

        n_dim = [1, 2, 3, 4, 5]
        p = CartesianPosition(n_dim)
        self.assertListEqual(list(p.values), n_dim)

        p = CartesianPosition(*n_dim)
        self.assertListEqual(list(p.values), n_dim)

    def test_gps_creation(self):
        values = [37.75134, -122.39488]
        p = GpsPosition(*values)
        self.assertListEqual(list(p.values), list(values))
        self.assertEqual(p.lat, values[0])
        self.assertEqual(p.lon, values[1])
        self.assertTupleEqual(p.lat_lon, tuple(values))

        p = GpsPosition()
        p.values = values
        self.assertListEqual(list(p.values), list(values))

        p = GpsPosition()
        p.lat = values[0]
        p.lon = values[1]
        self.assertListEqual(list(p.values), list(values))

    def test_cartesian_distance(self):
        p_1 = CartesianPosition(0.0, 0.0)
        p_2 = CartesianPosition(1.0, 1.0)
        dist = p_1.distance(p_1)
        self.assertEqual(round(dist, 4), 0.0)
        dist = p_1.distance(p_2)
        self.assertEqual(round(dist, 4), round(1.414214, 4))
        dist = p_2.distance(p_1)
        self.assertEqual(round(dist, 4), round(1.414214, 4))

        p_1 = CartesianPosition(7.0, 4.0, 3.0)
        p_2 = CartesianPosition(17.0, 6.0, 2.0)
        dist = p_1.distance(p_1)
        self.assertEqual(round(dist, 4), 0.0)
        dist = p_1.distance(p_2)
        self.assertEqual(round(dist, 4), round(10.246951, 4))

    def test_gps_distance(self):
        p_1 = GpsPosition(37.75134, -122.39488)
        p_2 = GpsPosition(37.75199, -122.3946)
        dist = p_1.distance(p_1)
        self.assertEqual(round(dist, 2), 0.0)
        dist = p_1.distance(p_2)
        self.assertEqual(round(dist, 2), round(76.35, 2))  # Distance in meters
        dist = p_2.distance(p_1)
        self.assertEqual(round(dist, 2), round(76.35, 2))

        p_2.values = [37.78435, -122.4126]
        dist = p_1.distance(p_2)
        self.assertEqual(round(dist, 2), round(3987.35, 2))

    def test_cartesian_intermediate(self):
        p_1 = CartesianPosition(0.0, 0.0)
        p_2 = CartesianPosition(2.0, 2.0)

        inter_p = p_1.intermediate(p_2, 0.0)
        self.assertIsInstance(inter_p, CartesianPosition)
        self.assertListEqual(list(inter_p.values), list(p_1.values))
        inter_p = p_1.intermediate(p_2, 1.0)
        self.assertListEqual(list(inter_p.values), list(p_2.values))
        inter_p = p_1.intermediate(p_2, 0.5)
        self.assertListEqual(list(inter_p.values), [1.0, 1.0])
        inter_p = p_2.intermediate(p_1, 0.5)
        self.assertListEqual(list(inter_p.values), [1.0, 1.0])

    def test_gps_distance(self):
        p_1 = GpsPosition(37.75134, -122.39488)
        p_2 = GpsPosition(37.78435, -122.4126)

        inter_p = p_1.intermediate(p_2, 0.0)
        self.assertIsInstance(inter_p, GpsPosition)
        self.assertListEqual(list(inter_p.values), list(p_1.values))
        inter_p = p_1.intermediate(p_2, 1.0)
        self.assertListEqual(list(inter_p.values), list(p_2.values))

        inter_values = [37.76778, -122.40361]
        inter_p = p_1.intermediate(p_2, 0.5)
        self.assertEqual(round(inter_p.lat, 3), round(inter_values[0], 3))
        self.assertEqual(round(inter_p.lon, 3), round(inter_values[1], 3))
        inter_p = p_2.intermediate(p_1, 0.5)
        self.assertEqual(round(inter_p.lat, 3), round(inter_values[0], 3))
        self.assertEqual(round(inter_p.lon, 3), round(inter_values[1], 3))


if __name__ == '__main__':
    unittest.main()
