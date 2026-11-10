import math
from haysim import Cell, ACT, YIELD, GOAL, S, TPS, run

SPIN = 6      # tick per giro del while di attesa
CHECK = 4     # tick di codice per reroll


def dist(a, b):
    dx = (b[0] - a[0]) % S
    dy = (b[1] - a[1]) % S
    return min(dx, S - dx) + min(dy, S - dy)


def block_origin(b):
    i = b % 8
    return 4 * i, (8 * (b // 8) + 4 * (i % 2)) % S


def spawn_tree(n):
    """run_range binario: restituisce per ogni blocco (ritardo di partenza in tick)."""
    start = {}
    def rr(lo, hi, t):
        while hi - lo > 1:
            mid = (lo + hi) // 2
            t += ACT
            rr(mid, hi, t)
            hi = mid
        start[lo] = t
    rr(0, n, 0)
    return start


def wait_grow(farm, cell, t, W, RES, fert=False, fert_min=0):
    """while not can_harvest(): if get_water()<W and tank>RES: use_item(Water)"""
    while True:
        r = cell.ready_at(t)
        if r <= t:
            return t
        if fert and r - t > fert_min and farm.fert(t) > 0:
            farm.fert_used += 1
            cell.prog = 1.0
            t = yield t + ACT
            continue
        if cell.w < W:
            if farm.tank(t) > RES:
                farm.water_used += 1
                cell.update(t)
                cell.w = min(1.0, cell.w + 0.25)
                t = yield t + ACT
                continue
            # aspetta il prossimo arrivo d'acqua o la maturazione
            from haysim import WATER_DT
            nxt = (math.floor(t / WATER_DT) + 1) * WATER_DT
            t2 = min(r, nxt)
        else:
            t2 = r
        t = yield t + max(SPIN, math.ceil((t2 - t) / SPIN) * SPIN)


def harvest_until_ok(farm, cell, pos, avoid, t):
    """harvest + reroll finche' il companion e' un bush non su 'avoid'."""
    while True:
        cell.update(t)
        if cell.prog >= 1 and cell.comp is not None and farm.valid(cell.comp):
            farm.hay += YIELD
            if farm.hay >= GOAL and farm.t_goal is None:
                farm.t_goal = t
        cell.prog = 0.0
        cell.t = t
        cell.comp = farm.roll(pos)
        t = yield t + ACT + CHECK
        if cell.comp[0] == 0 and cell.comp[1] != avoid:
            return t


def baseline(farm, W=0.68, RES=16, fert=False, fert_min=0, blocks=32):
    starts = spawn_tree(blocks)
    gens = []
    for b in range(blocks):
        gens.append((starts[b], drone(farm, b, W, RES, fert, fert_min)))
    return gens


def drone(farm, b, W, RES, fert, fert_min):
    t = yield
    bx, by = block_origin(b)
    pos = (0, 0)
    tgt = (bx, (by + 7) % S)
    t = yield t + dist(pos, tgt) * ACT
    # serpentina: 30 bush, 7 righe da 4 + 2 nella riga bassa
    x, y = bx, (by + 7) % S
    for k in range(7):
        d = 1 if k % 2 == 0 else -1
        for j in range(4):
            farm.bush.add((x % S, y))
            t = yield t + ACT
            if j < 3:
                x += d
                t = yield t + ACT
        y = (y - 1) % S
        t = yield t + ACT
    for _ in range(2):
        farm.bush.add((x % S, y))
        t = yield t + ACT
        x -= 1
        t = yield t + ACT
    west, east = (bx, by), (bx + 1, by)
    cw = farm.grass.setdefault(west, Cell())
    ce = farm.grass.setdefault(east, Cell())
    # parte sull'erba est
    while farm.hay < GOAL:
        t = yield from wait_grow(farm, ce, t, W, RES, fert, fert_min)
        t = yield from harvest_until_ok(farm, ce, east, west, t)
        t = yield t + ACT
        t = yield from wait_grow(farm, cw, t, W, RES, fert, fert_min)
        t = yield from harvest_until_ok(farm, cw, west, east, t)
        t = yield t + ACT + 3


if __name__ == "__main__":
    import sys, statistics
    for W in (0.5, 0.6, 0.68, 0.75, 0.85, 1.0):
        res = [run(baseline, seed=s, W=W)[0] for s in range(6)]
        print(f"W={W:.2f} media {statistics.mean(res):7.2f}s  {min(res):.2f}-{max(res):.2f}")
