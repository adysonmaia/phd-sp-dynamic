from sp.core.model import User
from sp.core.mobility.static import StaticMobility
from sp.core.mobility.track import TrackMobility
from sp.core.geometry.point.gps import GpsPoint, Point
import json
import unittest


class UsersFromFileTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/core/fixtures/test_users_from_file/users.json"
        users = None
        with open(filename) as json_file:
            users = []
            data = json.load(json_file)
            for item in data["users"]:
                users.append(User.from_json(item))
        cls.users = users

    def setUp(self):
        self.assertIsNotNone(self.users)

    def test_users_exists(self):
        self.assertEqual(len(self.users), 4)
        self.assertIsInstance(self.users[0], User)

    def test_users_properties(self):
        user = self.users[0]
        self.assertEqual(user.id, 0)
        self.assertEqual(user.app_id, 0)
        self.assertIsInstance(user.mobility, StaticMobility)
        pos = user.get_position(0)
        self.assertEqual(pos[0], 0.0)
        self.assertEqual(pos[1], 0.0)

        user = self.users[1]
        self.assertEqual(user.id, 1)
        self.assertEqual(user.app_id, 1)
        self.assertIsInstance(user.mobility, TrackMobility)
        self.assertEqual(len(user.mobility.tracks), 3)

        user = self.users[2]
        self.assertEqual(user.id, 2)
        self.assertEqual(user.app_id, 0)
        self.assertIsInstance(user.mobility, TrackMobility)
        self.assertEqual(len(user.mobility.tracks), 3)

        user = self.users[3]
        self.assertEqual(user.id, 3)
        self.assertEqual(user.app_id, 1)
        self.assertIsInstance(user.mobility, TrackMobility)
        self.assertEqual(len(user.mobility.tracks), 100)

    def test_update_position(self):
        user = self.users[1]

        pos = user.get_position(0)
        self.assertIsInstance(pos, Point)
        self.assertEqual(pos[0], 0.0)
        self.assertEqual(pos[1], 0.0)

        pos = user.get_position(1)
        self.assertIsInstance(pos, Point)
        self.assertEqual(pos[0], 0.0)
        self.assertEqual(pos[1], 1.0)

        pos = user.get_position(2)
        self.assertIsInstance(pos, Point)
        self.assertEqual(pos[0], 1.0)
        self.assertEqual(pos[1], 1.0)

        pos = user.get_position(3)
        self.assertIsNone(pos)

        pos = user.get_position(0)
        self.assertIsInstance(pos, Point)
        self.assertEqual(pos[0], 0.0)
        self.assertEqual(pos[1], 0.0)

    def test_interpolated_positions(self):
        user = self.users[2]

        # Saved values
        for i in [0, 2, 6]:
            pos = user.get_position(i)
            self.assertIsInstance(pos, Point)
            self.assertEqual(pos[0], float(i))
            self.assertEqual(pos[1], float(i))

        # Interpolated values
        for i in [1, 3, 4, 5]:
            pos = user.get_position(i)
            self.assertIsInstance(pos, Point)
            self.assertEqual(pos[0], float(i))
            self.assertEqual(pos[1], float(i))

        # Interpolated values with time tolerance
        tolerance = 1
        for i in [4, 8]:
            pos = user.get_position(i, tolerance=tolerance)
            self.assertIsNone(pos)
        for i in [1, 3, 5]:
            pos = user.get_position(i, tolerance=tolerance)
            self.assertIsInstance(pos, Point)
            self.assertEqual(pos[0], float(i))
            self.assertEqual(pos[1], float(i))

    def test_gps_positions(self):
        user = self.users[3]
        pos = user.get_position(1213084687)
        self.assertIsInstance(pos, GpsPoint)
        self.assertEqual(pos.lat, 37.75134)
        self.assertEqual(pos.lon, -122.39488)


if __name__ == '__main__':
    unittest.main()
