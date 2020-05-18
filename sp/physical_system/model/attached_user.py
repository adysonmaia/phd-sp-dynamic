from sp.core.model import User
from sp.core.geometry import Point


class AttachedUser(User):
    """Attached User Model Class

    It is a mobile user that is attached to a (edge/base station) node

    Attributes:
        node_id (int): node's id where the user is attached. None if the user is not attached to any node
        position (Point): current position of the user
    """

    def __init__(self):
        User.__init__(self)
        self.node_id = None
        self.position = None

    def get_current_position(self):
        """Get current position of the user

        Returns:
            Point: position
        """
        return self.position

    @staticmethod
    def from_user(user):
        """Create a Attached User from a User

        Args:
            user (User): original user
        Returns:
            AttachedUser: user with attached attributes
        """

        attached_user = AttachedUser()
        attached_user.id = user.id
        attached_user.app_id = user.app_id
        return attached_user


