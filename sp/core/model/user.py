from sp.core import mobility


class User:
    """User Model Class
    It is used to store properties of a user

    Attributes:
        id (int): Unique identification of the user
        app_id (int): Id of the application requested by the user
        mobility (sp.core.mobility.Mobility): user's mobility pattern
    """
    def __init__(self):
        self.id = -1
        self.app_id = -1
        self.mobility = None

    def get_position(self, time, tolerance=None):
        """ Get the user's position in specific time
        Args:
            time (float): simulation time
            tolerance (float): time tolerance to obtain the position or None to disregard this parameter
        Returns:
            sp.core.geometry.Point: user's position or None if the position is undefined for the specified time
        """
        if self.mobility is not None:
            return self.mobility.position(time, tolerance)
        else:
            return None

    @staticmethod
    def from_json(json_data):
        """Create a User object from a json data
        See :py:func:`sp.core.model.user.from_json`
        Args:
            json_data (dict): data loaded from a json
        Returns:
            User: loaded user
        """
        return from_json(json_data)


def from_json(json_data):
    """Create a User object from a json data

    The user's positions can be passed according to its mobility pattern and coordinate system
    See :py:func:`sp.core.mobility.from_json` and :py:func:`sp.core.geometry.point.from_json` for more detail
    In addition, the position can be passed as a external json file

    If a user is mobile, its position trace is passed a list of positions where each position is associated with a time

    E.g.:

    .. code-block:: python

        # Static position with Cartesian point passed as list [x, y]
        json_data = {'id':  0, 'app_id':  0, 'pos':  [0.0, 1.0]}
        user = sp.core.model.user.from_json(json_data)

        # Static position with Cartesian point passed as dict
        json_data = {'id':  0, 'app_id':  0, 'pos': {'x': 0.0, 'y': 1.0}}
        user = sp.core.model.user.from_json(json_data)

        # Static position with GPS point passed as dict
        json_data = {'id':  0, 'app_id':  0, 'pos': {'lat': 37.75134, 'lon': -122.39488}}
        user = sp.core.model.user.from_json(json_data)

        # Position in an external file
        json_data = {'id':  0, 'app_id':  0, 'pos': 'path/user_pos.json'},
        user = sp.core.model.user.from_json(json_data)

        # Mobile user with different positions over time
        json_data = {
            'id':  0, 'app_id':  0,
            # each item/position is saved as [x, y, time]
            'pos': [
                [0.0, 0.0, 0],  # time 0, position (x=0.0, y=0.0)
                [0.0, 0.0, 1],  # time 1, position (x=0.0, y=0.0)
                [1.0, 0.0, 2]  # time 2, position (x=1.0, y=0.0)
            ]
        }
        user = sp.core.model.user.from_json(json_data)

        # Mobile user with positions as dict
        # Cartesian point
        json_data = {
            'id':  0, 'app_id':  0,
            'pos': [
                {'x': 0.0, 'y': 0.0, 't': 0},  # time 0, position (x=0.0, y=0.0)
                {'x': 0.0, 'y': 0.0, 't': 1},  # time 1, position (x=0.0, y=0.0)
                {'x': 1.0, 'y': 0.0, 't': 2}  # time 2, position (x=1.0, y=0.0)
            ]
        }
        user = sp.core.model.user.from_json(json_data)

        # Mobile user with GPS positions
        json_data = {
            'id':  0, 'app_id':  0,
            'pos': [
                {'lat': 37.75134, 'lon': -122.39488, 't': 1213084687},
                {'lat': 37.75136, 'lon': -122.39527, 't': 1213084659},
                {'lat': 37.75199, 'lon': -122.3946, 't': 1213084540}
            ]
        }
        user = sp.core.model.user.from_json(json_data)

    Args:
         json_data (dict): data loaded from a json
    Returns:
        User: loaded user
    Raises:
        KeyError: Attribute not found
    """
    u = User()
    u.id = int(json_data["id"])
    u.app_id = int(json_data["app_id"])
    if "pos" in json_data:
        u.mobility = mobility.from_json(json_data["pos"])

    return u


