from sp.core.model.node import Node
from sp.core.estimator import AvgAggregatorEstimator
from sp.core.util.cached_property import cached_property
from statistics import mean


class GlobalNode(Node):
    """Global Node Model Class.

    It represents a subsystem/cluster containing a set o real nodes

    """

    def __init__(self):
        """Initialization
        """
        Node.__init__(self)
        self._nodes = {}
        self._central_node_id = None

    def _clear_cache(self):
        """Clear the cached properties
        """
        keys = ["nodes", "availability", "capacity", "cost"]
        for key in keys:
            if key in self.__dict__:
                del self.__dict__[key]

    @cached_property
    def nodes(self):
        """Get nodes in the cluster

        Returns:
            list: list of nodes
        """
        data = list(self._nodes.values())
        data.sort()
        return data

    @property
    def central_node_id(self):
        """Get central node's id

        Returns:
            int: node's id
        """
        if self._central_node_id is None:
            return self.nodes[0]
        else:
            return self._central_node_id

    @central_node_id.setter
    def central_node_id(self, node_id):
        self._central_node_id = node_id

    @property
    def central_node(self):
        """Get central node

        Returns:
            Node: node
        """
        node_id = self.central_node_id
        return self._nodes[node_id]

    @central_node.setter
    def central_node(self, node):
        """Set central node

        Args:
            node (Node): real node
        """
        if node is None:
            self.central_node_id = None
        else:
            self.central_node_id = node.id

    @cached_property
    def availability(self):
        """Get avg. availability among all nodes in the cluster

        Returns:
            float: availability
        """
        if len(self.nodes) == 0:
            return 0.0
        values = map(lambda n: n.availability, self.nodes)
        return mean(values)

    @cached_property
    def capacity(self):
        """Get avg. capacity among all nodes in the cluster

        Returns:
            dict: For each resource, it specifies the total capacity
        """
        capacity = {}
        resources = self.nodes[0].capacity.keys()
        for r in resources:
            values = [n.capacity[r] for n in self.nodes]
            capacity[r] = mean(values) if len(values) > 0 else 0.0
        return capacity

    @cached_property
    def cost(self):
        """Get avg. cost among all nodes in the cluster

        Returns:
            dict: For each resource, it presents a function to calculate the cost
        """
        cost = {}
        if len(self.nodes) == 0:
            return cost
        resources = self.nodes[0].capacity.keys()
        for r in resources:
            values = [n.cost[r] for n in self.nodes]
            estimator = AvgAggregatorEstimator(values)
            cost[r] = estimator
        return cost

    @cached_property
    def power_consumption(self):
        """Get avg. power consumption among all nodes in the cluster

        Returns:
            AvgAggregatorEstimator: estimation function
        """
        if len(self.nodes) == 0:
            return None
        values = [n.power_consumption for n in self.nodes]
        return AvgAggregatorEstimator(values)

    def add_node(self, node):
        """Add a node in the subsystem

        Args:
            node (Node): node
        """
        self._nodes[node.id] = node
        self._clear_cache()
