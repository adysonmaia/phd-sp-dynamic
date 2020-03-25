from . import Coverage
from sp.physical_system.model.attached_user import AttachedUser
import math


class CircleCoverage(Coverage):
    def __init__(self, radius=1000.0):
        self.radius = radius

    def update(self, system, environment, time_tolerance=None, distance_tolerance=None):
        time = system.time
        distance_tolerance = distance_tolerance if distance_tolerance is not None else 0.0
        attachments = {}

        for user in system.users:
            attached_node_id = None
            min_dist = math.inf
            user_pos = user.get_position(time, time_tolerance)

            if user_pos is not None:
                for node in system.bs_nodes:
                    node_pos = node.position

                    if node_pos is None:
                        continue

                    dist = user_pos.distance(node_pos)
                    if dist < min_dist + distance_tolerance and dist <= self.radius + distance_tolerance:
                        min_dist = dist
                        attached_node_id = node.id

            attached_user = AttachedUser.from_user(user)
            attached_user.node_id = attached_node_id
            attached_user.position = user_pos
            attachments[attached_user.id] = attached_user

        return attachments
