from . import Coverage


class MinDistCoverage(Coverage):
    def __init__(self, system=None):
        Coverage.__init__(self, system)

    def update(self, time):
        for user in self.system.users:
            node_id = -1
            min_dist = float("inf")
            if user.current_position is not None:
                for node in self.system.bs_nodes:
                    if node.current_position is not None:
                        dist = user.current_position.distance(node.current_position)
                        if dist < min_dist:
                            min_dist = dist
                            node_id = node.id
            user.node_id = node_id
