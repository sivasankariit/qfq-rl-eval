import math


def mean(l):
    if len(l) == 0:
        return 0
    return sum(l) * 1.0 / len(l)


def stdev(l, m=None):
    """
    @m is another mean with which we can measure stdev against.  Since
    this offers no guarantee that sq > m*m, I added an abs() before
    computing sqrt.
    """
    if m is None:
        m = mean(l)
    sq = mean(map(lambda e: e * e, l))
    return math.sqrt(abs(sq - m * m))
