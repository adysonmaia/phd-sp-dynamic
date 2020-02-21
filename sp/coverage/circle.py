from . import Coverage


class CircleCoverage(Coverage):
    def __init__(self, system=None, radius=1000.0):
        Coverage.__init__(self, system)
        self.radius = radius

    def update(self, time):
        for user in self.system.users:
            node_id = -1
            min_dist = float("inf")
            if user.current_position is not None:
                for node in self.system.bs_nodes:
                    if node.current_position is not None:
                        dist = user.current_position.distance(node.current_position)
                        if dist < min_dist and dist <= self.radius:
                            min_dist = dist
                            node_id = node.id
            user.node_id = node_id
