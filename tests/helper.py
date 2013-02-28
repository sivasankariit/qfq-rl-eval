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
    return vals, map(lambda n: n * 1.0 / total, nums)

def mean(l):
    return sum(l) * 1.0 / len(l)

def stdev(l):
    m = mean(l)
    sq = mean(map(lambda e: e * e, l))
    return math.sqrt(sq - m * m)
