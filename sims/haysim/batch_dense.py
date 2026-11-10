import sys, json, statistics, multiprocessing as mp
import micro
from haysim import run, TPS, ACT

import os
PLAN = json.load(open(os.environ.get("PLAN", "../dense/plan.json")))

def dense_setup(b):
    p = PLAN[b]
    return 1000 + (p["moves"] + p["plants"]) * ACT + 2 * p["moves"], tuple(p["A"]), tuple(p["C"])

def dense_bushes():
    g = set(tuple(c) for p in PLAN for c in p["pair"])
    s = set()
    for p in PLAN:
        for c in p["path"][1:-1]:
            s.add(tuple(c))
    return s

def one(args):
    layout, seed, kw = args
    if layout == "dense":
        micro.setup_cost = dense_setup
        B = dense_bushes()
    else:
        B = micro.bushes()
    def strat(farm):
        farm.end = None; farm.unripe = 0; farm.bush = B; farm.p2 = []; farm.spin = 0; farm.fert_used = 0
        return [(0, micro.drone_new(farm, b, **kw)) for b in range(32)]
    f = run(strat, seed=seed)[1]
    return f.end / TPS, f.unripe

if __name__ == "__main__":
    n = int(sys.argv[1])
    base = dict(WR=0.73, WN=2, EARLY=9, WC=1, A2=1)
    configs = [("old", base), ("dense", base)] + [("dense", dict(base, **eval(a))) for a in sys.argv[2:]]
    ref = None
    with mp.Pool() as pool:
        for lay, kw in configs:
            r = pool.map(one, [(lay, s, kw) for s in range(n)])
            ts = [x[0] for x in r]
            if ref is None: ref = ts
            d = [a - b for a, b in zip(ts, ref)]
            print(lay, {k: v for k, v in kw.items() if base.get(k) != v}, "media %.3f  diff %+.3f +- %.3f  unripe %d" % (statistics.mean(ts), statistics.mean(d), (statistics.stdev(d) / n ** .5) if any(d) else 0, sum(x[1] for x in r)), flush=True)
