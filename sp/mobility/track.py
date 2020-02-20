from . import Mobility
from sp import position
import copy


class TrackMobility(Mobility):
    def __init__(self, tracks=[]):
        Mobility.__init__(self)
        self.tracks = tracks
        self._current_position = None
        self._current_time = 0
        self._current_index = 0

    @property
    def current_position(self):
        return self._current_position

    def update_position(self, time):
        start = 0
        if time >= self._current_time:
            start = self._current_index
        tracks_len = len(self.tracks)

        new_pos = None
        new_index = start

        if tracks_len > 0:
            prev_tf = None
            next_tf = None

            for i in range(start, tracks_len):
                next_i = min(i + 1, tracks_len - 1)
                if self.tracks[i].time <= time <= self.tracks[next_i].time:
                    prev_tf = self.tracks[i]
                    next_tf = self.tracks[next_i]
                    new_index = i
                    break

            if prev_tf is not None and next_tf is not None:
                new_pos = prev_tf.position
                if prev_tf.time != time:
                    new_pos = prev_tf.intermediate(next_tf, time).position

        self._current_time = time
        self._current_index = new_index
        self._current_position = new_pos

    @classmethod
    def from_json(cls, json_data):
        return from_json(json_data)


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
    f.position = position.from_json(json_data)
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


