from sp.models import Topology, Node, Link
from sp.builders.topologies import TopologyFromFile
import unittest


class TopologyFromFileTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "./tests/fixtures/test_topology_from_file.json"
        cls.topology = TopologyFromFile(filename).build()

    def setUp(self):
        self.assertIsNotNone(self.topology)
        self.assertIsInstance(self.topology, Topology)

    def test_nodes_exists(self):
        self.assertEqual(len(self.topology.nodes), 4)
        self.assertIsInstance(self.topology.nodes[0], Node)
        self.assertEqual(len(self.topology.get_nodes_by_type("CLOUD")), 1)
        self.assertEqual(len(self.topology.get_nodes_by_type("CORE")), 1)
        self.assertEqual(len(self.topology.get_nodes_by_type("BS")), 2)

    def test_cloud_node(self):
        self.assertIsNotNone(self.topology.cloud_node)
        node = self.topology.cloud_node

        self.assertEqual(node.id, 0)
        self.assertEqual(node.type, "CLOUD")
        self.assertEqual(node.availability, 0.999)
        self.assertEqual(node.power_consumption, (200.0, 400.0))
        self.assertEqual(node.position, [0.0, 0.0])

        for resource in ["CPU", "RAM", "DISK"]:
            self.assertEqual(node.get_capacity(resource), float("INF"))
            self.assertEqual(node.get_cost(resource), (0.025, 0.025))

    def test_core_node(self):
        nodes = self.topology.get_nodes_by_type("CORE")
        self.assertEqual(len(nodes), 1)
        node = nodes[0]

        self.assertEqual(node.id, 1)
        self.assertEqual(node.type, "CORE")
        self.assertEqual(node.availability, 0.99)
        self.assertEqual(node.power_consumption, (50.0, 100.0))
        self.assertEqual(node.position, [0.0, 10.0])

        self.assertEqual(node.get_capacity("CPU"), 200.0)
        self.assertEqual(node.get_capacity("RAM"), 8000.0)
        self.assertEqual(node.get_capacity("DISK"), 32000.0)

        self.assertEqual(node.get_cost("CPU"), (0.05, 0.05))
        self.assertEqual(node.get_cost("RAM"), (0.05, 0.05))
        self.assertEqual(node.get_cost("DISK"), (0.05, 0.05))

    def test_bs_nodes(self):
        nodes = self.topology.get_bs_nodes()
        self.assertEqual(len(nodes), 2)

        for node in nodes:
            self.assertIn(node.id, [2, 3])
            self.assertEqual(node.type, "BS")
            self.assertEqual(node.availability, 0.9)
            self.assertEqual(node.power_consumption, (20.0, 50.0))
            self.assertIn(node.position, [[0.0, 11.0], [1.0, 10.0]])

            self.assertEqual(node.get_capacity("CPU"), 40.0)
            self.assertEqual(node.get_capacity("RAM"), 4000.0)
            self.assertEqual(node.get_capacity("DISK"), 16000.0)

            self.assertEqual(node.get_cost("CPU"), (0.1, 0.1))
            self.assertEqual(node.get_cost("RAM"), (0.1, 0.1))
            self.assertEqual(node.get_cost("DISK"), (0.1, 0.1))

    def test_links_exists(self):
        self.assertEqual(len(self.topology.links), 4)
        self.assertIsInstance(self.topology.links[0], Link)

        self.assertIsNotNone(self.topology.get_link(0, 1))
        self.assertIsNotNone(self.topology.get_link(1, 0))

        self.assertIsNotNone(self.topology.get_link(1, 2))
        self.assertIsNotNone(self.topology.get_link(1, 3))
        self.assertIsNotNone(self.topology.get_link(2, 3))

    def test_links_properties(self):
        link = self.topology.get_link(0, 1)
        self.assertEqual(link.bandwidth, 20000000000.0)
        self.assertEqual(link.propagation_delay, 10.0)

        link = self.topology.get_link(1, 2)
        self.assertEqual(link.bandwidth, 10000000000.0)
        self.assertEqual(link.propagation_delay, 1.0)

        link = self.topology.get_link(1, 3)
        self.assertEqual(link.bandwidth, 10000000000.0)
        self.assertEqual(link.propagation_delay, 1.0)

        link = self.topology.get_link(2, 3)
        self.assertEqual(link.bandwidth, 10000000000.0)
        self.assertEqual(link.propagation_delay, 1.4)

    def test_graph(self):
        self.assertIsNotNone(self.topology.graph)
        self.assertEqual(self.topology.graph.number_of_nodes(), 4)
        self.assertEqual(self.topology.graph.number_of_edges(), 4)
        self.assertIn(1, self.topology.graph.adj[0])
        self.assertIn(2, self.topology.graph.adj[1])
        self.assertIn(2, self.topology.graph.adj[3])
        self.assertIn(3, self.topology.graph.adj[1])
        self.assertIn(3, self.topology.graph.adj[2])


if __name__ == '__main__':
    unittest.main()
