from .circle import CircleCoverage

INF = float("inf")


class MinDistanceCoverage(CircleCoverage):
    def __init__(self):
        CircleCoverage.__init__(self, radius=INF)
