from abc import ABC, abstractmethod


class Routing(ABC):
    @abstractmethod
    def get_path(self, app_id, src_node_id, dst_node_id):
        return None

    @abstractmethod
    def get_path_length(self, app_id, src_node_id, dst_node_id):
        return None

    @abstractmethod
    def get_all_paths(self):
        return None

    @abstractmethod
    def get_all_paths_length(self):
        return None

    @abstractmethod
    def update(self, system, environment):
        pass
