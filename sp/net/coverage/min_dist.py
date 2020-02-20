from . import Coverage


class MinDistCoverage(Coverage):
    def __init__(self):
        Coverage.__init__(self)

    def update_connections(self, system):
        for user in system.users:
            node_id = -1
            if user.current_position is not None:
                for node in system.bs_nodes:
                    if node.current_position is None:
                        dist = user.current_position.distance(node.current_position)
                        if min_dist >= 0.0 and dist < min_dist:
                            min_dist = dist
                            node_id = node.id
            user.node_id = node_id