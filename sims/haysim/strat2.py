import math, statistics
from haysim import Cell, ACT, YIELD, GOAL, S, TPS, WATER_DT, run
import haysim
from strat import dist, block_origin, spawn_tree, SPIN, CHECK


class Done(Exception):
    pass


def wait_grow(farm, cell, t, W, RES):
    while True:
        if farm.end is not None and t >= farm.end:
            raise Done
        r = cell.ready_at(t)
        if r <= t:
            return t
        if cell.w < W and farm.tank(t) > RES:
            farm.water_used += 1
            cell.update(t)
            cell.w = min(1.0, cell.w + 0.25)
            t = yield t + ACT
            continue
        if cell.w < W:
            nxt = (math.floor(t / WATER_DT) + 1) * WATER_DT
            t2 = min(r, nxt)
        else:
            t2 = r
        t = yield t + max(SPIN, math.ceil((t2 - t) / SPIN) * SPIN)


def harvest_until_ok(farm, cell, pos, avoid, t, main):
    while True:
        cell.update(t)
        if cell.prog >= 1 and cell.comp is not None and farm.valid(cell.comp):
            farm.hay += YIELD
            if farm.hay >= GOAL and farm.t_goal is None:
                farm.t_goal = t
        cell.prog = 0.0
        cell.t = t
        cell.comp = farm.roll(pos)
        t = yield t + ACT + CHECK + (2 if main else 0)
        if farm.end is not None and t >= farm.end:
            raise Done
        if main and farm.hay >= GOAL:
            farm.end = t + ACT   # clear()
            raise Done
        if cell.comp[0] == 0 and cell.comp[1] != avoid:
            return t


def drone(farm, b, W, RES, prewater, W0, T0):
    t = yield
    main = b == 0
    bx, by = block_origin(b)
    t = yield t + dist((0, 0), (bx, (by + 7) % S)) * ACT
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
            w = W0 if t < T0 * TPS else W
            t = yield from wait_grow(farm, ce, t, w, RES)
            t = yield from harvest_until_ok(farm, ce, east, west, t, main)
            t = yield t + ACT
            t = yield from wait_grow(farm, cw, t, w, RES)
            t = yield from harvest_until_ok(farm, cw, west, east, t, main)
            t = yield t + ACT + 1
    except Done:
        return


def strategy(farm, W=0.68, RES=16, prewater=False, W0=None, T0=0):
    farm.end = None
    starts = spawn_tree(32)
    return [(starts[b], drone(farm, b, W, RES, prewater, W0 if W0 is not None else W, T0)) for b in range(32)]


def evaluate(n=6, **kw):
    out = []
    for s in range(n):
        farm = None
        def strat(f, **k):
            nonlocal farm
            farm = f
            return strategy(f, **k)
        last, f = run(strat, seed=s, **kw)
        out.append(farm.end / TPS)   # clear() chiude la run
    return statistics.mean(out)


if __name__ == "__main__":
    for kw in [dict(), dict(RES=0), dict(RES=4), dict(W=0.75), dict(W=0.6), dict(W=0.68, W0=0.4, T0=8),
               dict(W=0.68, W0=1.0, T0=8)]:
        print(kw, round(evaluate(**kw), 3))
