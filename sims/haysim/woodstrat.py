import math, statistics, sys
from woodsim import *


def dist(a, b):
    dx = (b[0] - a[0]) % S; dy = (b[1] - a[1]) % S
    return min(dx, S - dx) + min(dy, S - dy)


# ---------------- script dell'utente: colonne a scacchiera
def make_user(seed, W=0.5, RES=16):
    cells = [(x, y) for x in range(S) for y in range(S) if (x + y) % 2 == 0]
    farm = Farm(seed, cells)
    valid = lambda c: c[0] == 0 and (c[1][0] + c[1][1]) % 2 == 1
    gens = []
    def col(x):
        t = yield
        t = yield t + dist((0, 0), (x, x % 2)) * ACT
        y = x % 2
        for _ in range(16):
            p = (x, y)
            farm.plant(p, t); t = yield t + ACT
            farm.harvest  # noqa
            c = farm.cells[p]
            while c.w < W and farm.tank(t) > RES:
                farm.water_used += 1; c.w = min(1.0, c.w + 0.25); t = yield t + ACT
            # reroll: plant fallito (1) + harvest + plant
            while not valid(c.comp):
                t = yield t + 1 + 4
                farm.harvest(p, t); t = yield t + ACT
                farm.plant(p, t); t = yield t + ACT
            y = (y + 2) % S; t = yield t + 2 * ACT
        while True:
            for _ in range(16):
                p = (x, y)
                r = farm.ready_at(p, t)
                if r > t:
                    t = yield t + max(3, math.ceil((r - t) / 3) * 3)
                farm.harvest(p, t); t = yield t + ACT
                farm.plant(p, t); t = yield t + ACT + 4
                c = farm.cells[p]
                while not valid(c.comp):
                    t = yield t + 1 + 4
                    farm.harvest(p, t); t = yield t + ACT
                    farm.plant(p, t); t = yield t + ACT
                y = (y + 2) % S; t = yield t + 2 * ACT + 3
                if farm.wood >= GOAL:
                    farm.end = max(farm.end or 0, t)
                    return
    for x in range(S):
        gens.append((x * ACT if x else 31 * ACT, col(x)))
    return farm, gens


# ---------------- anelli su coppie di righe distanziate di 3, sfalsate di 1
ROWS = [0, 3, 6, 9, 12, 15, 18, 21, 24, 27]
def shift(y): return (ROWS.index(y)) % 2

def loops_layout(widths_per_pair):
    tours = []
    for pi, widths in enumerate(widths_per_pair):
        ya, yb = ROWS[2 * pi], ROWS[2 * pi + 1]
        x0 = 0
        for wdt in widths:
            k = wdt // 2
            A = [(x0 + 2 * j, ya) for j in range(k)]
            B = [(x0 + 1 + 2 * j, yb) for j in reversed(range(k))]
            tours.append(A + B)
            x0 += wdt
    return tours

LAYOUT = [[6, 6, 4, 4, 4, 4, 4]] * 2 + [[6, 6, 6, 6, 4, 4]] * 3


def make_loops(seed, W=1.0, RES=0, layout=None):
    tours = loops_layout(layout or LAYOUT)
    cells = [p for tr in tours for p in tr]
    farm = Farm(seed, cells)
    def valid(c):
        q = c[1]
        return c[0] == 0 and q not in farm.cells
    def drone(i, tour):
        t = yield
        main = i == 0
        pos = (0, 0)
        t = yield t + dist(pos, tour[0]) * ACT
        pos = tour[0]
        first = True
        try:
            while True:
                for p in tour:
                    t = yield t + dist(pos, p) * ACT
                    pos = p
                    if farm.cells[p].alive:
                        t = yield from water_wait(farm, p, t, W, RES)
                        farm.harvest(p, t); t = yield t + ACT
                        if main and farm.wood >= GOAL:
                            farm.end = t + ACT; return
                    else:
                        c = farm.cells[p]
                        while c.w < W and farm.tank(t) > RES and first:
                            farm.water_used += 1; c.w = min(1.0, c.w + 0.25); t = yield t + ACT
                    t = yield from plant_ok(farm, p, t, valid)
                    if farm.end is not None and t >= farm.end: return
                first = False
        finally:
            pass
    return farm, [(i * ACT, drone(i, tr)) for i, tr in enumerate(tours)]


def ev(make, n=3, **kw):
    out = []
    for s in range(n):
        f = run(make, seed=s, **kw)
        out.append(f.end / TPS)
    return statistics.mean(out), out


if __name__ == "__main__":
    which = sys.argv[1]
    if which == "user":
        print("user", ev(make_user))
    else:
        print("loops", ev(make_loops, W=float(sys.argv[2]) if len(sys.argv) > 2 else 1.0))
