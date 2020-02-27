class OptSolution:
    def __init__(self):
        self.app_placement = {}
        self.allocated_resource = {}
        self.load_distribution = {}
        self.received_load = {}

    def get_app_placement(self, app_id, node_id):
        return self.app_placement[app_id][node_id]

    def get_load_distribution(self, app_id, src_node_id, dst_node_id):
        return self.load_distribution[app_id][src_node_id][dst_node_id]

    def get_allocated_resource(self, app_id, node_id, resource_name):
        return self.allocated_resource[app_id][node_id][resource_name]

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
