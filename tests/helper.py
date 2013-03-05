import math

def cdf(lst):
    vals = []
    nums = []
    cum = 0
    for val, num in lst:
        cum += num
        vals.append(val)
        nums.append(cum)
    return vals, map(lambda n: n*1.0/cum, nums)

def cdf_list(lst):
    lst.sort()
    prev = None
    prev_count = 0
    vals = []
    nums = []
    total = 0
    for val in lst:
        if prev is None:
            prev = val
        if val == prev:
            prev_count += 1
        else:
            vals.append(prev)
            total += prev_count
            nums.append(total)
            prev = val
            prev_count = 1
    vals.append(prev)
    total += prev_count
    nums.append(total)
    if total == 0:
        return [], []
    return vals, map(lambda n: n * 1.0 / total, nums)

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
