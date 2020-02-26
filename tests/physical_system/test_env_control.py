from sp.core.model import Scenario
from sp.physical_system.model import SystemState, EnvironmentInput
from sp.physical_system import EnvironmentController
from sp.physical_system.routing.shortest_path import Routing, ShortestPathRouting
from sp.physical_system.coverage import Coverage
from sp.physical_system.coverage.min_distance import MinDistanceCoverage
from sp.physical_system.estimator import LinkDelayEstimator, DefaultLinkDelayEstimator
from sp.physical_system.estimator import RequestLoadEstimator, DefaultRequestLoadEstimator
from sp.physical_system.estimator import AppQueueSizeEstimator, DefaultAppQueueSizeEstimator
import json
import unittest


class EnvControlTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/physical_system/fixtures/test_env_control.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = SystemState()
            system.scenario = Scenario.from_json(data)
        cls.system = system

    def setUp(self):
        self.assertIsInstance(self.system, SystemState)
        self.assertEqual(len(self.system.nodes), 4)
        self.assertEqual(len(self.system.bs_nodes), 2)
        self.assertEqual(len(self.system.users), 10)
        self.assertEqual(len(self.system.apps), 3)

    def test_env_start(self):
        control = EnvironmentController()

        time = 0
        self.system.time = time
        control.start()

        self.assertIsInstance(control.routing, Routing)
        self.assertIsInstance(control.coverage, Coverage)
        self.assertIsInstance(control.link_delay_estimator, LinkDelayEstimator)
        self.assertIsInstance(control.req_load_estimator, RequestLoadEstimator)
        self.assertIsInstance(control.app_queue_size_estimator, AppQueueSizeEstimator)

    def test_env_update(self):
        control = EnvironmentController()
        control.routing = ShortestPathRouting()
        control.coverage = MinDistanceCoverage()
        control.link_delay_estimator = DefaultLinkDelayEstimator()
        control.req_load_estimator = DefaultRequestLoadEstimator()
        control.queue_size_estimator = DefaultAppQueueSizeEstimator()

        control.start()
        for time in [0, 1]:
            self.system.time = time
            env_input = control.update(self.system)
            self.system.environment = env_input

            self.assertIsInstance(env_input, EnvironmentInput)
            self.assertIsNotNone(env_input.request_load)
            self.assertIsNotNone(env_input.net_delay)
            self.assertIsNotNone(env_input.net_path)
            self.assertIsNotNone(env_input.app_queue_size)
            self.assertIsNotNone(env_input.attached_users)

            for app in self.system.apps:
                for src_node in self.system.nodes:
                    queue_size = env_input.get_app_queue_size(app.id, src_node.id)
                    self.assertEqual(queue_size, 0.0)

                    load = env_input.get_request_load(app.id, src_node.id)
                    nb_users = env_input.get_nb_users(app.id, src_node.id)
                    if src_node.is_base_station():
                        self.assertGreater(load, 0.0)
                        self.assertGreater(nb_users, 0)
                    else:
                        self.assertEqual(load, 0.0)
                        self.assertEqual(nb_users, 0)

                    for dst_node in self.system.nodes:
                        delay = env_input.get_net_delay(app.id, src_node.id, dst_node.id)
                        path = env_input.get_net_path(app.id, src_node.id, dst_node.id)
                        if src_node.id == dst_node.id:
                            self.assertEqual(delay, 0.0)
                            self.assertEqual(len(path), 0.0)
                        else:
                            self.assertGreater(delay, 0.0)
                            self.assertGreater(len(path), 0.0)


if __name__ == '__main__':
    unittest.main()
