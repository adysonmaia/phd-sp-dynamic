from sp.model import System, Scenario, Environment
from sp.controller.environment import DefaultEnvironmentController
from sp.routing.shortest_path import Routing, ShortestPathRouting
from sp.coverage.min_dist import Coverage, MinDistCoverage
from sp.estimator.link_delay import LinkDelayEstimator, DefaultLinkDelayEstimator
from sp.estimator.request_load import RequestLoadEstimator, DefaultRequestLoadEstimator
from sp.estimator.queue_size import QueueSizeEstimator, DefaultQueueSizeEstimator
import json
import unittest


class EnvControlTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "./tests/fixtures/test_env_control.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
        cls.system = system

    def setUp(self):
        self.assertIsInstance(self.system, System)
        self.assertEqual(len(self.system.nodes), 4)
        self.assertEqual(len(self.system.bs_nodes), 2)
        self.assertEqual(len(self.system.users), 10)
        self.assertEqual(len(self.system.apps), 3)

        for node in self.system.nodes:
            self.assertIsNotNone(node.current_position)

    def test_env_start(self):
        control = DefaultEnvironmentController()

        time = 0
        self.system.time = time
        control.init_params(self.system)

        self.assertIsInstance(control.system, System)
        self.assertIsInstance(control.routing, Routing)
        self.assertIsInstance(control.coverage, Coverage)
        self.assertIsInstance(control.link_delay_estimator, LinkDelayEstimator)
        self.assertIsInstance(control.req_load_estimator, RequestLoadEstimator)
        self.assertIsInstance(control.queue_size_estimator, QueueSizeEstimator)

    def test_env_update(self):
        control = DefaultEnvironmentController()
        control.routing = ShortestPathRouting()
        control.coverage = MinDistCoverage()
        control.link_delay_estimator = DefaultLinkDelayEstimator()
        control.req_load_estimator = DefaultRequestLoadEstimator()
        control.queue_size_estimator = DefaultQueueSizeEstimator()

        for time in [0, 1]:
            self.system.time = time
            control.init_params(self.system)
            env_model = control.update(self.system)
            self.system.environment = env_model

            self.assertIsInstance(env_model, Environment)
            self.assertIsNotNone(env_model.request_load)
            self.assertIsNotNone(env_model.net_delay)
            self.assertIsNotNone(env_model.net_path)
            self.assertIsNotNone(env_model.app_queue_size)

            for app in self.system.apps:
                for src_node in self.system.nodes:
                    queue_size = env_model.get_app_queue_size(app.id, src_node.id)
                    self.assertEqual(queue_size, 0.0)

                    load = env_model.get_request_load(app.id, src_node.id)
                    if src_node.is_base_station():
                        self.assertGreater(load, 0.0)
                    else:
                        self.assertEqual(load, 0.0)

                    for dst_node in self.system.nodes:
                        delay = env_model.get_net_delay(app.id, src_node.id, dst_node.id)
                        path = env_model.get_net_path(app.id, src_node.id, dst_node.id)
                        if src_node.id == dst_node.id:
                            self.assertEqual(delay, 0.0)
                            self.assertEqual(len(path), 0.0)
                        else:
                            self.assertGreater(delay, 0.0)
                            self.assertGreater(len(path), 0.0)


if __name__ == '__main__':
    unittest.main()
