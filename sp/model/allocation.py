class Allocation:
    def __init__(self):
        self.app_placement = {}
        self.allocated_resource = {}
        self.load_distribution = {}

    def get_app_placement(self, app_id, node_id):
        return self.app_placement[app_id][node_id]

    def set_app_placement(self, app_id, node_id, value):
        self.app_placement[app_id][node_id] = bool(value)

    def get_load_distribution(self, app_id, src_node_id, dst_node_id):
        return self.app_placement[app_id][src_node_id][dst_node_id]

    def set_load_distribution(self, app_id, src_node_id, dst_node_id, value):
        self.app_placement[app_id][src_node_id][dst_node_id] = float(value)

    def get_allocated_resource(self, app_id, node_id, resource_name):
        return self.allocated_resource[app_id][node_id][resource_name]

    def set_allocated_resource(self, app_id, node_id, resource_name, value):
        self.allocated_resource[app_id][node_id][resource_name] = float(value)

    @classmethod
    def create_empty(cls, system):
        alloc = Allocation()

        for app in system.apps:
            alloc.app_placement[app.id] = {}
            alloc.allocated_resource[app.id] = {}
            alloc.load_distribution[app.id] = {}
            for node in system.nodes:
                alloc.app_placement[app.id][node.id] = False
                alloc.allocated_resource[app.id][node.id] = {}
                alloc.load_distribution[app.id][node.id] = {}

                for resource in system.resources:
                    alloc.allocated_resource[app.id][node.id][resource.name] = 0.0

                for dst_node in system.nodes:
                    alloc.load_distribution[app.id][node.id][dst_node.id] = 0.0

        return alloc
