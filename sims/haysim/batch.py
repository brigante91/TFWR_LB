import sys, statistics, multiprocessing as mp
import micro
from haysim import run, TPS

def one(args):
    which, seed, kw = args
    d = micro.drone_old if which == "old" else micro.drone_new
    B = micro.bushes()
    def strat(farm):
        farm.end = None; farm.unripe = 0; farm.bush = B; farm.p2 = []; farm.spin = 0; farm.fert_used = 0
        return [(0, d(farm, b, **kw)) for b in range(32)]
    f = run(strat, seed=seed)[1]
    return f.end / TPS, f.unripe

if __name__ == "__main__":
    n = int(sys.argv[1])
    configs = [("old", {}), ("new", {})] + [("new", eval(a)) for a in sys.argv[2:]]
    base = None
    with mp.Pool() as pool:
        for which, kw in configs:
            r = pool.map(one, [(which, s, kw) for s in range(n)])
            ts = [x[0] for x in r]
            if base is None:
                base = ts
            d = [a - b for a, b in zip(ts, base)]
            print(which, kw, "media %.3f  diff vs old %+.4f +- %.4f  unripe %d" % (statistics.mean(ts), statistics.mean(d), statistics.stdev(d) / n ** 0.5 if any(d) else 0, sum(x[1] for x in r)), flush=True)
