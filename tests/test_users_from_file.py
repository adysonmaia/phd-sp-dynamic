from sp.model.user import User
from sp.mobility.static import StaticMobility
from sp.mobility.track import TrackMobility
from sp.geometry.point.gps import GpsPoint
import json
import unittest


class UsersFromFileTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "./tests/fixtures/test_users_from_file/users.json"
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
        self.assertEqual(user.node_id, -1)
        self.assertIsInstance(user.mobility, StaticMobility)
        user.update_position(0)
        self.assertEqual(user.current_position[0], 0.0)
        self.assertEqual(user.current_position[1], 0.0)

        user = self.users[1]
        self.assertEqual(user.id, 1)
        self.assertEqual(user.app_id, 1)
        self.assertEqual(user.node_id, -1)
        self.assertIsInstance(user.mobility, TrackMobility)
        self.assertEqual(len(user.mobility.tracks), 3)

        user = self.users[2]
        self.assertEqual(user.id, 2)
        self.assertEqual(user.app_id, 0)
        self.assertEqual(user.node_id, -1)
        self.assertIsInstance(user.mobility, TrackMobility)
        self.assertEqual(len(user.mobility.tracks), 3)

        user = self.users[3]
        self.assertEqual(user.id, 3)
        self.assertEqual(user.app_id, 1)
        self.assertEqual(user.node_id, -1)
        self.assertIsInstance(user.mobility, TrackMobility)
        self.assertEqual(len(user.mobility.tracks), 100)

    def test_update_position(self):
        user = self.users[1]

        user.update_position(0)
        self.assertIsNotNone(user.current_position)
        self.assertEqual(user.current_position[0], 0.0)
        self.assertEqual(user.current_position[1], 0.0)

        user.update_position(1)
        self.assertIsNotNone(user.current_position)
        self.assertEqual(user.current_position[0], 0.0)
        self.assertEqual(user.current_position[1], 1.0)

        user.update_position(2)
        self.assertIsNotNone(user.current_position)
        self.assertEqual(user.current_position[0], 1.0)
        self.assertEqual(user.current_position[1], 1.0)

        user.update_position(3)
        self.assertIsNone(user.current_position)

        user.update_position(0)
        self.assertIsNotNone(user.current_position)
        self.assertEqual(user.current_position[0], 0.0)
        self.assertEqual(user.current_position[1], 0.0)

    def test_interpolated_positions(self):
        user = self.users[2]

        # Saved values
        for i in [0, 2, 5]:
            user.update_position(i)
            self.assertIsNotNone(user.current_position)
            self.assertEqual(user.current_position[0], float(i))
            self.assertEqual(user.current_position[1], float(i))

        # Interpolated values
        for i in [1, 3, 4]:
            user.update_position(i)
            self.assertIsNotNone(user.current_position)
            self.assertEqual(user.current_position[0], float(i))
            self.assertEqual(user.current_position[1], float(i))

    def test_gps_positions(self):
        user = self.users[3]
        user.update_position(1213084687)
        self.assertIsInstance(user.current_position, GpsPoint)
        self.assertEqual(user.current_position.lat, 37.75134)
        self.assertEqual(user.current_position.lon, -122.39488)


if __name__ == '__main__':
    unittest.main()
