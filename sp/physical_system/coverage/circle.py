from . import Coverage
from sp.physical_system.model.attached_user import AttachedUser

INF = float("inf")


class CircleCoverage(Coverage):
    def __init__(self, radius=1000.0):
        Coverage.__init__(self)
        self.radius = radius

    def update(self, system, environment):
        time = system.time
        attachments = {}

        for user in system.users:
            attached_node_id = None
            min_dist = INF
            user_pos = user.get_position(time)

            if user_pos is not None:
                for node in system.bs_nodes:
                    node_pos = node.position

                    if node_pos is None:
                        continue

                    dist = user_pos.distance(node_pos)
                    if dist < min_dist and dist <= self.radius:
                        min_dist = dist
                        attached_node_id = node.id

            attached_user = AttachedUser.from_user(user)
            attached_user.node_id = attached_node_id
            attached_user.position = user_pos
            attachments[attached_user.id] = attached_user

        return attachments
