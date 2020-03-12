from sp.core.model import ControlInput


class OptSolution(ControlInput):
    def __init__(self):
        ControlInput.__init__(self)
        self.received_load = {}

    def get_received_load(self, app_id, node_id):
        return self.received_load[app_id][node_id]

    @staticmethod
    def create_empty(system):
        solution = OptSolution()

        for app in system.apps:
            solution.app_placement[app.id] = {}
            solution.allocated_resource[app.id] = {}
            solution.load_distribution[app.id] = {}
            solution.received_load[app.id] = {}
            for node in system.nodes:
                solution.app_placement[app.id][node.id] = False
                solution.allocated_resource[app.id][node.id] = {}
                solution.load_distribution[app.id][node.id] = {}
                solution.received_load[app.id][node.id] = 0.0

                for resource in system.resources:
                    solution.allocated_resource[app.id][node.id][resource.name] = 0.0

                for dst_node in system.nodes:
                    solution.load_distribution[app.id][node.id][dst_node.id] = 0.0

        return solution
