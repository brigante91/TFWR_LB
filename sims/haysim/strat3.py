import statistics
import strat2
from strat2 import *
from strat import dist, block_origin


def start_of(b):
    bx, by = block_origin(b)
    return (bx, (by + 7) % S)


def sched_old(n=32):
    """run_range classico: figli nati in (0,0); restituisce b -> (t_inizio_lavoro_blocco)."""
    out = {}
    def rr(lo, hi, t):
        while hi - lo > 1:
            mid = (lo + hi) // 2
            t += ACT
            rr(mid, hi, t)
            hi = mid
        out[lo] = t + dist((0, 0), start_of(lo)) * ACT
    rr(0, n, 0)
    return out


def sched_new(n=32):
    """Ogni sotto-albero va prima all'inizio del suo primo blocco e genera li' i figli."""
    out = {}
    def task(lo, hi, t, pos):
        t += dist(pos, start_of(lo)) * ACT
        pos = start_of(lo)
        while hi - lo > 1:
            mid = (lo + hi) // 2
            t += ACT
            task(mid, hi, t, pos)
            hi = mid
        out[lo] = t
    task(0, n, 0, (0, 0))
    return out


def drone_at(farm, b, t0, W, RES):
    """come strat2.drone ma senza goto: parte gia' all'inizio del blocco al tempo t0."""
    t = yield
    main = b == 0
    bx, by = block_origin(b)
    x, y = bx, (by + 7) % S
    for k in range(7):
        d = 1 if k % 2 == 0 else -1
        for j in range(4):
            farm.bush.add((x % S, y)); t = yield t + ACT
            if j < 3:
                x += d; t = yield t + ACT
        y = (y - 1) % S; t = yield t + ACT
    for _ in range(2):
        farm.bush.add((x % S, y)); t = yield t + ACT
        x -= 1; t = yield t + ACT
    west, east = (bx, by), (bx + 1, by)
    cw = farm.grass.setdefault(west, Cell())
    ce = farm.grass.setdefault(east, Cell())
    try:
        while True:
            t = yield from wait_grow(farm, ce, t, W, RES)
            t = yield from harvest_until_ok(farm, ce, east, west, t, main)
            t = yield t + ACT
            t = yield from wait_grow(farm, cw, t, W, RES)
            t = yield from harvest_until_ok(farm, cw, west, east, t, main)
            t = yield t + ACT + 1
    except Done:
        return


def strategy(farm, W=0.68, RES=0, sched=sched_new):
    farm.end = None
    st = sched()
    return [(st[b], drone_at(farm, b, st[b], W, RES)) for b in range(32)]


def evaluate(strategy, n=6, **kw):
    out = []
    for s in range(n):
        box = {}
        def f(farm, **k):
            box['f'] = farm
            return strategy(farm, **k)
        run(f, seed=s, **kw)
        out.append(box['f'].end / TPS)
    return statistics.mean(out)


if __name__ == "__main__":
    so, sn = sched_old(), sched_new()
    print("avvio medio old", statistics.mean(so.values()) / TPS, "new", statistics.mean(sn.values()) / TPS)
    print("old", round(evaluate(strategy, sched=sched_old), 3))
    print("new", round(evaluate(strategy, sched=sched_new), 3))
