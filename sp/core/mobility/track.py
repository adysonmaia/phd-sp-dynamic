from .mobility import Mobility
from sp.core.geometry import point
from functools import total_ordering
import copy
import math


class TrackMobility(Mobility):
    def __init__(self, tracks=None):
        Mobility.__init__(self)
        self.tracks = []
        if tracks is not None:
            self.tracks = tracks

    def position(self, time, tolerance=None):
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
        return from_json(json_data)


@total_ordering
class TrackFrame:
    def __init__(self, pos=None, time=0):
        self.position = pos
        self.time = time

    def __eq__(self, other):
        return self.time == other.time

    def __lt__(self, other):
        return self.time < other.time

    def __str__(self):
        return "t: {} p: {}".format(self.time, self.position)

    def intermediate(self, other_frame, time):
        inter_pos = None
        delta_time = abs(float(other_frame.time - self.time))
        if delta_time != 0.0:
            fraction = (time - self.time) / delta_time
            inter_pos = self.position.intermediate(other_frame.position, fraction)
        else:
            inter_pos = copy.deepcopy(self.position)
        return TrackFrame(inter_pos, time)


def _frame_from_json(json_data):
    f = TrackFrame()
    f.position = point.from_json(json_data)
    if isinstance(json_data, list):
        f.time = int(json_data[2])
    elif isinstance(json_data, dict) and "time" in json_data:
        f.time = int(json_data["time"])
    elif isinstance(json_data, dict) and "t" in json_data:
        f.time = int(json_data["t"])
    else:
        raise TypeError

    return f


def from_json(json_data):
    tracks_frame = []
    for item in json_data:
        f = _frame_from_json(item)
        tracks_frame.append(f)

    tracks_frame.sort()
    return TrackMobility(tracks_frame)


