from sp.core.model import User


class AttachedUser(User):
    def __init__(self):
        User.__init__(self)
        self.node_id = None
        self.position = None

    def get_current_position(self):
        return self.position

    @staticmethod
    def from_user(user):
        attached_user = AttachedUser()
        attached_user.id = user.id
        attached_user.app_id = user.app_id
        return attached_user


