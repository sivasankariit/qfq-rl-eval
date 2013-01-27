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

def plot_cdf(x, y, **opts):
    #plt.figure()
    plt.plot(x, y, **opts)
    if args.xlog:
        plt.xscale("log")
    #plt.show()

def mean(l):
    return sum(l) * 1.0 / len(l)

def stdev(l):
    m = mean(l)
    sq = mean(map(lambda e: e * e, l))
    return math.sqrt(sq - m * m)
