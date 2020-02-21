class Routing:
    def __init__(self, system=None):
        self.system = system

    def get_path(self, app_id, src_node_id, dst_node_id):
        return None

    def get_path_length(self, app_id, src_node_id, dst_node_id):
        return None

    def get_all_paths(self, app_id):
        return None

    def update(self, time):
        pass