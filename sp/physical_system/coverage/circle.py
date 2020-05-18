from .coverage import Coverage
from sp.physical_system.model.attached_user import AttachedUser
import math


class CircleCoverage(Coverage):
    """Circle Coverage

    It attaches an user to the nearest (edge/base station) node.
    The attachment only occurs if the distance between user and node is less than the specified radius

    Attributes:
        radius (float): maximum distance between an user and a node. In meters if the GPS coordination system is used
    """

    def __init__(self, radius=1000.0):
        """Initialization

        Args:
            radius (float): circle's radius
        """
        self.radius = radius

    def update(self, system, environment_input, time_tolerance=None, distance_tolerance=None):
        """Update attachment of users in a system's state and environment input

        Args:
            system (sp.core.model.system.System): system's state
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
            time_tolerance (float): time tolerance (in seconds)
            distance_tolerance (float): distance tolerance. In meters if the GPS coordination system is used

        Returns:
            dict: attached users indexed by their ids
        """

        time = system.time
        distance_tolerance = distance_tolerance if distance_tolerance is not None else 0.0
        attachments = {}

        for user in system.users:
            attached_node_id = None
            min_dist = math.inf
            user_pos = user.get_position(time, time_tolerance=time_tolerance)

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
