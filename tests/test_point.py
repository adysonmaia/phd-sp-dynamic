from sp.geometry.point.cartesian import CartesianPoint
from sp.geometry.point.gps import GpsPoint
import unittest


class PointTestCase(unittest.TestCase):
    def test_cartesian_creation(self):
        values = [10.5, 50.1]
        p = CartesianPoint(values)
        self.assertListEqual(list(p.values), values)
        self.assertEqual(p[0], values[0])
        self.assertEqual(p[1], values[1])
        self.assertEqual(p.x, values[0])
        self.assertEqual(p.y, values[1])

        p = CartesianPoint(*values)
        self.assertListEqual(list(p.values), values)

        p = CartesianPoint()
        p.values = values
        self.assertListEqual(list(p.values), values)

        p = CartesianPoint()
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
        p = CartesianPoint(n_dim)
        self.assertListEqual(list(p.values), n_dim)

        p = CartesianPoint(*n_dim)
        self.assertListEqual(list(p.values), n_dim)

    def test_gps_creation(self):
        values = [-122.39488, 37.75134]  # [lon, lat]
        p = GpsPoint(*values)
        self.assertListEqual(list(p.values), list(values))
        self.assertEqual(p.lat, values[GpsPoint.LAT_INDEX])
        self.assertEqual(p.lon, values[GpsPoint.LON_INDEX])
        self.assertTupleEqual(p.lon_lat, tuple(values))
        self.assertTupleEqual(p.lat_lon, tuple(values[::-1]))

        p = GpsPoint()
        p.values = values
        self.assertListEqual(list(p.values), list(values))

        p = GpsPoint()
        p.lat = values[GpsPoint.LAT_INDEX]
        p.lon = values[GpsPoint.LON_INDEX]
        self.assertListEqual(list(p.values), list(values))

    def test_cartesian_distance(self):
        p_1 = CartesianPoint(0.0, 0.0)
        p_2 = CartesianPoint(1.0, 1.0)
        dist = p_1.distance(p_1)
        self.assertEqual(round(dist, 4), 0.0)
        dist = p_1.distance(p_2)
        self.assertEqual(round(dist, 4), round(1.414214, 4))
        dist = p_2.distance(p_1)
        self.assertEqual(round(dist, 4), round(1.414214, 4))

        p_1 = CartesianPoint(7.0, 4.0, 3.0)
        p_2 = CartesianPoint(17.0, 6.0, 2.0)
        dist = p_1.distance(p_1)
        self.assertEqual(round(dist, 4), 0.0)
        dist = p_1.distance(p_2)
        self.assertEqual(round(dist, 4), round(10.246951, 4))

    def test_gps_distance(self):
        p_1 = GpsPoint(lat=37.75134, lon=-122.39488)
        p_2 = GpsPoint(lat=37.75199, lon=-122.3946)
        dist = p_1.distance(p_1)
        self.assertEqual(round(dist, 2), 0.0)
        dist = p_1.distance(p_2)
        self.assertEqual(round(dist, 2), round(76.35, 2))  # Distance in meters
        dist = p_2.distance(p_1)
        self.assertEqual(round(dist, 2), round(76.35, 2))

        p_2.values = [-122.4126, 37.78435]  # [lon, lat]
        dist = p_1.distance(p_2)
        self.assertEqual(round(dist, 2), round(3987.35, 2))

    def test_cartesian_intermediate(self):
        p_1 = CartesianPoint(0.0, 0.0)
        p_2 = CartesianPoint(2.0, 2.0)

        inter_p = p_1.intermediate(p_2, 0.0)
        self.assertIsInstance(inter_p, CartesianPoint)
        self.assertListEqual(list(inter_p.values), list(p_1.values))
        inter_p = p_1.intermediate(p_2, 1.0)
        self.assertListEqual(list(inter_p.values), list(p_2.values))
        inter_p = p_1.intermediate(p_2, 0.5)
        self.assertListEqual(list(inter_p.values), [1.0, 1.0])
        inter_p = p_2.intermediate(p_1, 0.5)
        self.assertListEqual(list(inter_p.values), [1.0, 1.0])

    def test_gps_intermediate(self):
        p_1 = GpsPoint(lat=37.75134, lon=-122.39488)
        p_2 = GpsPoint(lat=37.78435, lon=-122.4126)

        inter_p = p_1.intermediate(p_2, 0.0)
        self.assertIsInstance(inter_p, GpsPoint)
        self.assertListEqual(list(inter_p.values), list(p_1.values))
        inter_p = p_1.intermediate(p_2, 1.0)
        self.assertListEqual(list(inter_p.values), list(p_2.values))

        inter_values = [-122.40361, 37.76778]  # [lon, lat]
        inter_p = p_1.intermediate(p_2, 0.5)
        self.assertEqual(round(inter_p.lat, 3), round(inter_values[GpsPoint.LAT_INDEX], 3))
        self.assertEqual(round(inter_p.lon, 3), round(inter_values[GpsPoint.LON_INDEX], 3))
        inter_p = p_2.intermediate(p_1, 0.5)
        self.assertEqual(round(inter_p.lat, 3), round(inter_values[GpsPoint.LAT_INDEX], 3))
        self.assertEqual(round(inter_p.lon, 3), round(inter_values[GpsPoint.LON_INDEX], 3))


if __name__ == '__main__':
    unittest.main()
