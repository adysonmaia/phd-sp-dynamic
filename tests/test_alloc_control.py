from sp.model import System, Scenario, Node, Allocation
from sp.controller.environment import EnvironmentController, DefaultEnvironmentController
from sp.controller.allocation import PeriodicAllocationController
from sp.solver.static.cloud import Solver, CloudSolver
import json
import unittest


class AllocControlTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "./tests/fixtures/test_alloc_control.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
        cls.system = system
        cls.env_ctl = DefaultEnvironmentController()

    def setUp(self):
        self.assertIsInstance(self.system, System)
        self.assertIsInstance(self.env_ctl, EnvironmentController)
        self.assertEqual(len(self.system.nodes), 4)
        self.assertEqual(len(self.system.bs_nodes), 2)
        self.assertEqual(len(self.system.users), 10)
        self.assertEqual(len(self.system.apps), 3)
        self.assertIsInstance(self.system.cloud_node, Node)

    def test_periodic_start(self):
        alloc_ctr = PeriodicAllocationController()

        time = 0
        self.system.time = time
        self.env_ctl.start(self.system)

        alloc_ctr.start(self.system)
        self.assertIsInstance(alloc_ctr.system, System)
        self.assertIsInstance(alloc_ctr.solver, Solver)
        self.assertEqual(alloc_ctr.next_update, time)
        self.assertGreater(alloc_ctr.period, 0)

        alloc_ctr.stop()

    def test_periodic_update(self):
        alloc_ctr = PeriodicAllocationController()
        alloc_ctr.solver = CloudSolver()

        for period in [1, 2]:
            alloc_ctr.period = period

            time = 0
            self.system.time = time
            self.env_ctl.start(self.system)
            alloc_ctr.start(self.system)

            for time in range(4):
                self.system.time = time
                self.env_ctl.update(time)

                self.system.allocation = None
                updated = (alloc_ctr.next_update == time)
                alloc_ctr.update(time)
                if updated:
                    self.assertIsInstance(self.system.allocation, Allocation)
                    self.assertEqual(alloc_ctr.next_update, time + period)
                else:
                    self.assertIsNone(self.system.allocation)

            self.env_ctl.stop()
            alloc_ctr.stop()


if __name__ == '__main__':
    unittest.main()
