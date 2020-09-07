from sp.core.model import ControlInput


class OptSolution(ControlInput):
    """Optimization Solution Class Model

    A solution is a control input with cached attributes

    Attributes:
        received_load (dict): cached received load
    """

    def __init__(self):
        """Initialization
        """
        ControlInput.__init__(self)
        self.received_load = {}

    def get_received_load(self, app_id, node_id):
        """Get received load for an application in a node

        Args:
            app_id (int): application's id
            node_id (int): node's id

        Returns:
            float: load
        """
        return self.received_load[app_id][node_id]

    @classmethod
    def create_empty(cls, system):
        """Create a empty solution for a system's scenario

        Args:
            system (sp.core.model.system.System): system

        Returns:
            OptSolution: solution
        """
        solution = cls()

        for app in system.apps:
            solution.app_placement[app.id] = {}
            solution.allocated_resource[app.id] = {}
            solution.load_distribution[app.id] = {}
            solution.received_load[app.id] = {}
            for node in system.nodes:
                solution.app_placement[app.id][node.id] = 0
                solution.allocated_resource[app.id][node.id] = {}
                solution.load_distribution[app.id][node.id] = {}
                solution.received_load[app.id][node.id] = 0.0

                for resource in system.resources:
                    solution.allocated_resource[app.id][node.id][resource.name] = 0.0

                for dst_node in system.nodes:
                    solution.load_distribution[app.id][node.id][dst_node.id] = 0.0

        return solution
