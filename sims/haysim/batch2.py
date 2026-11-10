"""Confronta varianti di dsim con le stesse sequenze di companion.
uso: python3 batch2.py N "dict(pre_a=1)" "dict(W0=0.5)" ...   (PLAN=... per un altro piano)"""
import sys, os, statistics, multiprocessing as mp
import dsim

PLAN = dsim.load_plan(os.environ.get("PLAN", dsim.PLAN_OPT))
BASEPLAN = dsim.load_plan(dsim.PLAN_OPT)

def one(args):
    kw, seed = args
    P = dict(dsim.BASE, plan=BASEPLAN)
    P.update(kw)
    if "plan" in kw:
        P["plan"] = dsim.load_plan(kw["plan"]) if isinstance(kw["plan"], str) else kw["plan"]
    elif os.environ.get("PLAN"):
        P["plan"] = PLAN
    T, f = dsim.run_once(P, seed)
    return T, f.unripe, f.nwater, f.waited, f.waitw, f.notyet

def main():
    n = int(sys.argv[1])
    configs = [{}] + [eval(a) for a in sys.argv[2:]]
    ref = None
    with mp.Pool() as pool:
        for kw in configs:
            r = pool.map(one, [(kw, s) for s in range(n)])
            ts = [x[0] for x in r]
            if ref is None:
                ref = ts
            d = [a - b for a, b in zip(ts, ref)]
            sd = statistics.stdev(d) / n ** 0.5 if n > 1 and any(d) else 0.0
            print("%-60s media %.3f  diff %+.4f +- %.4f  unripe %.1f  acqua %.0f  attese %.0f  fallite %.0f  notyet %.1f" % (
                str(kw)[:60], statistics.mean(ts), statistics.mean(d), sd,
                statistics.mean(x[1] for x in r), statistics.mean(x[2] for x in r),
                statistics.mean(x[3] for x in r), statistics.mean(x[4] for x in r), statistics.mean(x[5] for x in r)), flush=True)

if __name__ == "__main__":
    main()
