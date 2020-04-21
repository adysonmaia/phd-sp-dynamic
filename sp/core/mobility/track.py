from .mobility import Mobility
from sp.core.geometry import point
from functools import total_ordering
import copy
import math


class TrackMobility(Mobility):
    """Track Mobility
    It stores a list of positions attached to a timestamp

    Attributes:
        tracks (list(TrackFrame)): list of tracks frame. A frame store the position at a specific time
    """
    def __init__(self, tracks=None):
        Mobility.__init__(self)
        self.tracks = []
        if tracks is not None:
            self.tracks = tracks

    def position(self, time, tolerance=None):
        """Get position at a specific time and with certain time tolerance

        If the specified time isn't stored in the tracks frame, a position is calculated based on the interpolation
        of two consecutive track frame f1 and f2 such that (f1.time <= time <= f2.time). The interpolation is
        calculated only if (time - f1.time <= tolerance or f2.time - time <= tolerance)

        Args:
            time (float): time
            tolerance (float): a time tolerance to obtain a interpolated position between two consecutive track frame.
                If None, the tolerance is set to infinity
        Returns:
            point.Point: position or None if position is not found
        """

        start = 0
        tracks_len = len(self.tracks)
        position = None
        tolerance = tolerance if tolerance is not None else math.inf

        if tracks_len > 0:
            prev_tf = None
            next_tf = None
            first_tf = self.tracks[0]
            last_tf = self.tracks[-1]

            for i in range(start, tracks_len):
                next_i = min(i + 1, tracks_len - 1)
                if self.tracks[i].time <= time <= self.tracks[next_i].time:
                    prev_tf = self.tracks[i]
                    next_tf = self.tracks[next_i]
                    break

            interpolate = prev_tf is not None and next_tf is not None
            interpolate = interpolate and (time - prev_tf.time <= tolerance or next_tf.time - time <= tolerance)
            if interpolate:
                position = prev_tf.position
                if prev_tf.time != time:
                    position = prev_tf.intermediate(next_tf, time).position
            elif tolerance is not None and not math.isinf(tolerance):
                if abs(time - first_tf.time) <= tolerance:
                    position = first_tf.position
                elif abs(time - last_tf.time) <= tolerance:
                    position = last_tf.position

        return position

    @staticmethod
    def from_json(json_data):
        """Create Track Mobility from a json data
        See :py:func:`sp.core.mobility.track.from_json`
        Args:
            json_data (list): data loaded from a json
        Returns:
            TrackMobility: loaded mobility
        """
        return from_json(json_data)


@total_ordering
class TrackFrame:
    """Track Frame
    It stores the position at a specific time

    Attributes:
        position (point.Point): position
        time (float): time
    """
    def __init__(self, position=None, time=0.0):
        """Initialization
        Args:
            position (point.Point): position
            time (float): time
        """
        self.position = position
        self.time = time

    def __eq__(self, other):
        return self.time == other.time

    def __lt__(self, other):
        return self.time < other.time

    def __str__(self):
        return "t: {} p: {}".format(self.time, self.position)

    def intermediate(self, other_frame, time):
        """Interpolate a position from a time between two frames

        Args:
            other_frame (TrackFrame): next frame
            time (float): a time between self.time and other_frame.time
        Returns:
            TrackFrame: frame with the interpolated position
        """
        inter_pos = None
        delta_time = abs(float(other_frame.time - self.time))
        if delta_time != 0.0:
            fraction = (time - self.time) / delta_time
            inter_pos = self.position.intermediate(other_frame.position, fraction)
        else:
            inter_pos = copy.deepcopy(self.position)
        return TrackFrame(inter_pos, time)


def _frame_from_json(json_data):
    """Create Track Frame from a json data
    Args:
        json_data (Union[list, dict]): loaded data from json
    Returns:
        TrackFrame: loaded track frame
    Raises:
        KeyError: attributes not found
    """
    f = TrackFrame()
    f.position = point.from_json(json_data)
    if isinstance(json_data, list):
        f.time = int(json_data[2])
    elif isinstance(json_data, dict) and "time" in json_data:
        f.time = int(json_data["time"])
    elif isinstance(json_data, dict) and "t" in json_data:
        f.time = int(json_data["t"])
    else:
        raise KeyError

    return f


def from_json(json_data):
    """Create a Track Mobility from a json data
    Args:
        json_data (list): loaded data from json
    Returns:
        TrackMobility: loaded mobility
    Raises:
        KeyError: attributes not found
    """
    tracks_frame = []
    for item in json_data:
        f = _frame_from_json(item)
        tracks_frame.append(f)

    tracks_frame.sort()
    return TrackMobility(tracks_frame)


