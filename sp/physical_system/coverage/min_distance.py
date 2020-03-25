from .circle import CircleCoverage
import math


class MinDistanceCoverage(CircleCoverage):
    def __init__(self):
        CircleCoverage.__init__(self, radius=math.inf)
