from .circle import Coverage, CircleCoverage
import math


class MinDistanceCoverage(CircleCoverage):
    """Minimum Distance Coverage

    It attaches an user to the nearest (edge/base station) node
    """

    def __init__(self):
        """Initialization
        """
        CircleCoverage.__init__(self, radius=math.inf)
