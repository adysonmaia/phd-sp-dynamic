from sp.core.util import json_util
from collections.abc import Iterable
import numpy as np
import math


def min_max_bound(y, min_value=0.0, max_value=1.0):
    """Bound a collection of values or a single value between an upper and lower limit

    Args:
        y (Union[Iterable, float]): collection of values or a single value
        min_value (float): minimum value
        max_value (float): maximum value

    Returns:
        list: bounded values
    """

    def min_max_value(v):
        return min(max_value, max(min_value, v))

    if isinstance(y, list) or isinstance(y, np.ndarray) or isinstance(y, Iterable):
        y = list(map(min_max_value, y))
    else:
        y = min_max_value(y)
    return y


def add_white_noise(y, noise=None, bound=True, scale=False):
    """Add a gaussian white noise process with zero mean and constant variance to a list o values

    Args:
        y (Union[list, np.ndarray]): list of values between 0 and 1
        noise (float): standard deviation of the noise
        bound (bool): if resulted values will be bounded between 0 and 1
        scale (bool): if resulted values will be scaled between 0 and 1. It only works if the bound parameter is False

    Returns:
        list: list of values resulted of noise addition
    """
    if noise:
        mean = 0.0
        e = np.random.normal(mean, noise, len(y))
        y = np.add(y, e)
        if bound:
            y = min_max_bound(y)
        elif scale:
            y = scale_samples(y)
    return y


def add_samples(*ys):
    """Add a list of list of values between 0 and 1.
    The resulting added values are scaled to a range between 0 and 1

    Args:
        *ys: each parameter is a list of values

    Returns:
        list: list of values after the addition and scale operation
    """

    ys_len = len(ys)
    if ys_len == 0:
        return []
    elif ys_len == 1:
        return ys[0]

    y = ys[0]
    for i in range(1, ys_len):
        y = np.add(y, ys[i])
    y = scale_samples(y, min_value=0.0, max_value=ys_len)
    return y


def scale_samples(y, min_scale=0.0, max_scale=1.0, min_value=None, max_value=None):
    """Scale a list of values to be in a range between min_scale and max_scale

    Args:
        y (Iterable): list of values
        min_scale (float): minimum value after the scale operation
        max_scale (float): maximum value after the scale operation
        min_value (float): minimum value before the scale operation. If None, it looks in the specified list of values
        max_value (float): maximum value before the scale operation. If None, it looks in the specified list of values

    Returns:
        list: list of scaled values
    """

    if min_value is None:
        min_value = min(y)
    if max_value is None:
        max_value = max(y)
    delta_ratio = 0.0
    if max_value != min_value:
        delta_ratio = float(max_scale - min_scale) / float(max_value - min_value)

    def scale_value(v):
        return (v - min_value) * delta_ratio + min_scale

    y = list(map(scale_value, y))
    return y


def random_birth_death_process(birth_rate=.5, death_rate=.5, nb_samples=None, noise=None):
    """Generate random samples according to a (Kendall) birth and death process.

    Args:
        birth_rate (float): birth rate (probability) as a value between 0 and 1
        death_rate (float): death rate (probability) as a value between 0 and 1
        nb_samples (int): number of generated samples. If None, function returns only a single value
        noise (float): it adds a white noise to the generated values if this parameter is not None

    Returns:
        Union[list, float]: list of random values or a single value if nb_samples is None.
            Resulted values are between 0 and 1
    """

    n = 100
    # a = birth_rate / float(n)
    # b = death_rate / float(n)

    nb_steps = nb_samples if nb_samples else 1
    y = np.zeros(nb_steps)

    if birth_rate > death_rate:
        y[0] = np.random.randint(0, n // 2)
    elif birth_rate < death_rate:
        y[0] = np.random.randint(n // 2, n + 1)
    else:
        y[0] = np.random.randint(0, n + 1)

    for i in range(nb_steps - 1):
        # birth = np.random.rand() <= a * y[i]
        # death = np.random.rand() <= b * y[i]

        birth = np.random.rand() <= birth_rate
        death = np.random.rand() <= death_rate

        y[i + 1] = y[i]
        if y[i] < n and birth:
            y[i + 1] += 1
        if y[i] > 0 and death:
            y[i + 1] -= 1

    y = [v / float(n) for v in y]
    y = add_white_noise(y, noise)

    if nb_samples is None:
        return y[0]
    else:
        return y


def random_burst(normal_value=None, burst_value=1.0, normal_transition=0.5, burst_transition=0.5,
                 nb_samples=None, noise=None):
    """Generate random samples according to a burst model.
    A burst model follows a markov chain with two states (normal and burst state), where each state is
    associated with a generated value.

    Args:
        normal_value (float): generated value during the normal state. If None, a random value is selected
        burst_value (float): generated value during the burst state
        normal_transition (float): transition probability from normal state to burst state
        burst_transition (float): transition probability from burst state to normal state
        nb_samples (int): number of generated samples. If None, function returns only a single value
        noise (float): it adds a white noise to the generated values if this parameter is not None

    Returns:
        Union[list, float]: list of random values or a single value if nb_samples is None.
            Resulted values are between 0 and 1
    """

    if normal_value is None:
        # factors = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        factors = [0.1, 0.2, 0.3, 0.4, 0.5]
        factor = np.random.choice(factors)
        normal_value = np.random.uniform(0.0, burst_value * factor)

    v = [normal_value, burst_value]
    p = [normal_transition, burst_transition]

    nb_steps = nb_samples if nb_samples else 1
    y = np.zeros(nb_steps)
    s = np.random.choice([0, 1])

    for i in range(nb_steps):
        if np.random.rand() <= p[s]:
            s = 1 - s
        y[i] = v[s]

    y = scale_samples(y, min_value=0.0)
    y = add_white_noise(y, noise)

    if nb_samples is None:
        return y[0]
    else:
        return y


def random_linear(nb_samples=None, noise=None):
    """Generate random samples following a linear function

    Args:
        nb_samples (int): number of generated samples. If None, function returns only a single value
        noise (float): it adds a white noise to the generated values if this parameter is not None

    Returns:
        Union[list, float]: list of values or a single value if nb_samples is None.
            Resulted values are between 0 and 1
    """
    a = np.random.uniform(0.0, 1.0)
    # b_param_options = [(0.0, 1.0), (a, 1.0), (0.0, a), (a, a)]
    # b_param_index = np.random.choice(range(len(b_param_options)))
    # b_param = b_param_options[b_param_index]
    # b = np.random.uniform(*b_param)
    b = 0.0
    if a <= 0.5:
        b = 1.0
    else:
        b = 0.0

    nb_steps = nb_samples if nb_samples else 1
    y = np.linspace(a, b, num=nb_steps)
    y = add_white_noise(y, noise)

    if nb_samples is None:
        return y[0]
    else:
        return y


def random_constant(value=None, nb_samples=None, noise=None):
    """Generate a constant value

    Args:
        value (float): constant value between 0 and 1. If None, a random value is choose
        nb_samples (int): number of generated samples. If None, function returns only a single value
        noise (float): it adds a white noise to the generated values if this parameter is not None

    Returns:
        Union[list, float]: list of values or a single value if nb_samples is None.
            Resulted values are between 0 and 1
    """
    if value is None:
        value = np.random.uniform(0.0, 1.0)
    else:
        value = min_max_bound(value)

    nb_steps = nb_samples if nb_samples else 1
    y = [value for _ in range(nb_steps)]
    y = add_white_noise(y, noise)

    if nb_samples is None:
        return y[0]
    else:
        return y


def random_uniform(nb_samples=None, noise=None):
    """Generate random values following an uniform distribution

    Args:
        nb_samples (int): number of generated samples. If None, function returns only a single value
        noise (float): it adds a white noise to the generated values if this parameter is not None

    Returns:
        Union[list, float]: list of random values or a single value if nb_samples is None.
            Resulted values are between 0 and 1
    """
    nb_steps = nb_samples if nb_samples else 1
    y = np.random.uniform(0, 1, nb_steps)
    y = add_white_noise(y, noise)

    if nb_samples is None:
        return y[0]
    else:
        return y


def random_beta_pdf(alpha=2, beta=3, nb_samples=None, noise=None):
    """Generate values of the beta distribution's probability density function

    Args:
        alpha (float): alpha parameter of the beta distribution
        beta (float): beta parameter of the beta distribution
        nb_samples (int): number of generated samples. If None, function returns only a single value
        noise (float): it adds a white noise to the generated values if this parameter is not None

    Returns:
        Union[list, float]: list of random values or a single value if nb_samples is None.
            Resulted values are between 0 and 1
    """
    bin_size = 100
    nb_steps = nb_samples if nb_samples else 1
    size = nb_steps * bin_size

    s = np.random.beta(alpha, beta, size)
    hist, bin_edges = np.histogram(s, nb_steps, density=False)

    max_v = float(max(hist))
    y = [v / max_v for v in hist]
    y = add_white_noise(y, noise)

    if nb_samples is None:
        return y[0]
    else:
        return y


def random_cycle(period=None, nb_samples=None, noise=None):
    """Generate cycled values according to a trigonometric function

    Args:
        period (float): cycle's period
        nb_samples (int): number of generated samples. If None, function returns only a single value
        noise (float): it adds a white noise to the generated values if this parameter is not None

    Returns:
        Union[list, float]: list of random values or a single value if nb_samples is None.
            Resulted values are between 0 and 1
    """

    nb_steps = nb_samples if nb_samples else 1
    period = period if period else nb_steps
    
    amplitude = 1.0
    w = 2 * np.pi / float(period)
    theta = np.random.uniform(0.0, math.pi)
    alpha = amplitude * math.cos(theta)
    beta = amplitude * math.sin(theta)

    y = np.zeros(nb_steps)
    for i in range(nb_steps):
        y[i] = alpha * math.cos(w * i) + beta * math.sin(w * i)

    y = scale_samples(y)
    y = add_white_noise(y, noise)

    if nb_samples is None:
        return y[0]
    else:
        return y


def random_zipf(alpha=1.8, nb_samples=None, noise=None):
    """Generate random values according to a zeta (zipf) distribution

    Args:
        alpha (float): shape parameter, it must be greater than 1
        nb_samples (int): number of generated samples. If None, function returns only a single value
        noise (float): it adds a white noise to the generated values if this parameter is not None

    Returns:
        Union[list, float]: list of random values or a single value if nb_samples is None.
            Resulted values are between 0 and 1
    """
    nb_steps = nb_samples if nb_samples else 1
    y = np.random.zipf(alpha, nb_steps)

    y_sum = sum(y)
    y = scale_samples(y, min_value=0.0, max_value=y_sum)
    y = add_white_noise(y, noise)

    if nb_samples is None:
        return y[0]
    else:
        return y


def random_time_series(time_series, nb_samples=None, noise=None, min_value=None, max_value=None):
    """Generate values from a time series

    Args:
        time_series (Union[list,str]): time series or filename for the time series
        nb_samples (int): number of generated samples. If None, function returns only a single value
        noise (float): it adds a white noise to the generated values if this parameter is not None
        min_value (float): minimum value that will be zero after the scaling
        max_value (float): maximum value that will be one after the scaling

    Returns:
        Union[list, float]: list of random values or a single value if nb_samples is None.
            Resulted values are between 0 and 1
    """
    time_series = json_util.load_content(time_series)
    ts_size = len(time_series)

    nb_steps = nb_samples if nb_samples else 1
    indexes = np.linspace(0, ts_size - 1, num=nb_steps)
    indexes = map(lambda i: int(round(i)), indexes)
    y = [time_series[i] for i in indexes]

    y = scale_samples(y, min_value=min_value, max_value=max_value)
    y = add_white_noise(y, noise)

    if nb_samples is None:
        return y[0]
    else:
        return y
