from collections.abc import Iterable
import math


def inv_exp_aggregator(values):
    """Inverted Exponential Aggregator.

    .. math::

        \sum_{i=0}^{|v| -1}v[i]/e^i


    Args:
        values (Iterable): list of values
    Returns:
        float: aggregated value
    """
    result = 0.0
    index = 0
    for value in values:
        result += value / math.exp(index)
        index += 1
    return result


def sum_aggregator(values):
    """Sum Aggregator.

    .. math::

        \sum_{i=0}^{|v| -1}v[i]


    Args:
        values (Iterable): list of values
    Returns:
        float: aggregated value
    """
    return sum(values) if values else 0.0
