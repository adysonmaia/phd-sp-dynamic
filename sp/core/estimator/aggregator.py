from .estimator import Estimator
from statistics import mean


class AvgAggregatorEstimator(Estimator):
    """Aggregator Estimator

    """

    def __init__(self, estimators=None):
        """Initialization

        Args:
            estimators (list): list of estimators
        """
        Estimator.__init__(self)
        self.estimators = estimators
        if self.estimators is None:
            self.estimators = []

    def calc(self, *args, **kwargs):
        """Calculate the estimation

        Args:
            *args: args
            **kwargs: kwargs
        Returns:
            object: estimation result
        """
        if len(self.estimators) == 0:
            return None

        values = map(lambda f: f.calc(*args, **kwargs), self.estimators)
        return mean(values)
