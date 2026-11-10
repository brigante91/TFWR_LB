"""Confronto di piani/parametri su dsim con le stesse sequenze di companion.
uso: BASE=plan_split3_16.json python3 sweep_chk.py N [piano[:dict(...)]] ..."""
import sys, os, statistics, multiprocessing as mp
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib
dsim = importlib.import_module(os.environ.get("SIM", "dsim"))
D = os.path.join(HERE, "..", "dense") + "/"
BASE = os.environ.get("BASE", "plan_split3_16.json")


def one(args):
    plan, kw, seed = args
    P = dict(dsim.BASE, plan=dsim.load_plan(D + plan), dict_lit=True, ret_water=1)
    P.update(kw)
    T, f = dsim.run_once(P, seed)
    return T, f.unripe, f.nwater, f.waited, f.chk_hit, f.chk_bad, f.chk_unripe, (sum(getattr(f, "q4end", [])) / 32 if getattr(f, "q4end", []) else 0)


if __name__ == "__main__":
    n = int(sys.argv[1])
    configs = [(BASE, {})]
    for a in sys.argv[2:]:
        plan, kw = a.split(":", 1) if ":" in a else (a, "{}")
        configs.append((plan or BASE, eval(kw)))
    ref = None
    with mp.Pool(int(os.environ.get("PROCS", "0")) or None) as pool:
        for plan, kw in configs:
            r = pool.map(one, [(plan, kw, s) for s in range(n)])
            ts = [x[0] for x in r]
            if ref is None:
                ref = ts
            d = [a - b for a, b in zip(ts, ref)]
            sd = statistics.stdev(d) / n ** .5 if any(d) else 0
            print("%-22s %-28s media %.3f diff %+.3f +- %.3f unripe %d acqua %d chk validi/vuoti/acerbi %.1f/%.1f/%.1f fine4 %.1fs" % (
                plan, kw, statistics.mean(ts), statistics.mean(d), sd, sum(x[1] for x in r), sum(x[2] for x in r) / n,
                sum(x[4] for x in r) / n, sum(x[5] for x in r) / n, sum(x[6] for x in r) / n, sum(x[7] for x in r) / n), flush=True)
