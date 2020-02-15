from sp.builders.applications import ApplicationsFromFile
from sp.models import Application
import unittest


class AppsFromFileCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "./tests/fixtures/test_apps_from_file.json"
        cls.apps = ApplicationsFromFile(filename).build()

    def setUp(self):
        self.assertIsNotNone(self.apps)

    def test_apps_exists(self):
        self.assertEqual(len(self.apps), 3)
        self.assertIsInstance(self.apps[0], Application)

    def test_embb_app(self):
        app = None
        for item in self.apps:
            if item.type == "EMBB":
                app = item
                break
        self.assertIsNotNone(app)

        self.assertEqual(app.id, 0)
        self.assertEqual(app.deadline, 100.0)
        self.assertEqual(app.work_size, 10.0)
        self.assertEqual(app.data_size, 8000000)
        self.assertEqual(app.request_rate, 0.01)
        self.assertEqual(app.availability, 0.99)
        self.assertEqual(app.max_instances, 1000)
        self.assertEqual(app.get_demand("CPU"), (10.0, 1.0))
        self.assertEqual(app.get_demand("RAM"), (1.0, 50.0))
        self.assertEqual(app.get_demand("DISK"), (1.0, 50.0))

    def test_urllc_app(self):
        app = None
        for item in self.apps:
            if item.type == "URLLC":
                app = item
                break
        self.assertIsNotNone(app)

        self.assertEqual(app.id, 1)
        self.assertEqual(app.deadline, 10.0)
        self.assertEqual(app.work_size, 5.0)
        self.assertEqual(app.data_size, 8000)
        self.assertEqual(app.request_rate, 0.1)
        self.assertEqual(app.availability, 0.999)
        self.assertEqual(app.max_instances, 1000)
        self.assertEqual(app.get_demand("CPU"), (5.0, 0.5))
        self.assertEqual(app.get_demand("RAM"), (1.0, 10.0))
        self.assertEqual(app.get_demand("DISK"), (1.0, 10.0))

    def test_mmtc_app(self):
        app = None
        for item in self.apps:
            if item.type == "MMTC":
                app = item
                break
        self.assertIsNotNone(app)

        self.assertEqual(app.id, 2)
        self.assertEqual(app.deadline, 1000.0)
        self.assertEqual(app.work_size, 5.0)
        self.assertEqual(app.data_size, 8000)
        self.assertEqual(app.request_rate, 0.001)
        self.assertEqual(app.availability, 0.9)
        self.assertEqual(app.max_instances, 1000)
        self.assertEqual(app.get_demand("CPU"), (5.0, 0.005))
        self.assertEqual(app.get_demand("RAM"), (1.0, 10.0))
        self.assertEqual(app.get_demand("DISK"), (1.0, 10.0))


if __name__ == '__main__':
    unittest.main()
