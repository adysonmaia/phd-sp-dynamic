class ControlInput:
    def __init__(self):
        self.app_placement = {}
        self.allocated_resource = {}
        self.load_distribution = {}

    def get_app_placement(self, app_id, node_id):
        return self.app_placement[app_id][node_id]

    def get_load_distribution(self, app_id, src_node_id, dst_node_id):
        return self.load_distribution[app_id][src_node_id][dst_node_id]

    def get_allocated_resource(self, app_id, node_id, resource_name):
        return self.allocated_resource[app_id][node_id][resource_name]

    @staticmethod
    def from_opt_solution(solution):
        control = ControlInput()
        control.app_placement = solution.app_placement
        control.allocated_resource = solution.allocated_resource
        control.load_distribution = solution.load_distribution
        return control
