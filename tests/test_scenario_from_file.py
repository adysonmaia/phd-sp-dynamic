from sp.model.scenario import Scenario
from sp.model.application import Application
from sp.model.topology import Topology
from sp.model.node import Node
from sp.model.link import Link
from sp.model.user import User
from sp.model.resource import Resource
import json
import unittest


class ScenarioFromFileCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "./tests/fixtures/test_scenario_from_file.json"
        scenario = None
        with open(filename) as json_file:
            data = json.load(json_file)
            scenario = Scenario.from_json(data)
        cls.scenario = scenario

    def setUp(self):
        self.assertIsInstance(self.scenario, Scenario)

    def test_properties(self):
        self.assertGreater(len(self.scenario.apps), 0)
        self.assertIsInstance(self.scenario.apps[0], Application)

        self.assertGreater(len(self.scenario.users), 0)
        self.assertIsInstance(self.scenario.users[0], User)

        self.assertGreater(len(self.scenario.resources), 0)
        self.assertIsInstance(self.scenario.resources[0], Resource)

        self.assertIsInstance(self.scenario.topology, Topology)
        self.assertGreater(len(self.scenario.nodes), 0)
        self.assertIsInstance(self.scenario.nodes[0], Node)

        self.assertGreater(len(self.scenario.links), 0)
        self.assertIsInstance(self.scenario.links[0], Link)
