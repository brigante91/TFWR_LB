import sys, statistics, math
from woodsim import *
from woodstrat import dist

ROWS12 = [0, 3, 6, 8, 11, 14, 16, 19, 22, 24, 27, 30]


def tours12():
    """6 coppie di righe; in ogni coppia 5 anelli da 6 alberi (colonne 0..29),
    piu' 2 droni sul giro delle colonne 30/31 (12 alberi, 6 ciascuno)."""
    tours = []
    for pi in range(6):
        ya, yb = ROWS12[2 * pi], ROWS12[2 * pi + 1]
        sa = (2 * pi) % 2; sb = 1 - sa   # riga A pari, riga B dispari
        for L in range(5):
            x0 = 6 * L
            A = [(x0 + 2 * j, ya) for j in range(3)]
            B = [(x0 + 1 + 2 * j, yb) for j in reversed(range(3))]
            tours.append(A + B)
    rest = []
    for i, y in enumerate(ROWS12):
        rest.append((30 if i % 2 == 0 else 31, y))
    tours.append(rest[:6]); tours.append(rest[6:])
    return tours


def make12(seed, W=0.9, RES=0, tours=None):
    tours = tours or tours12()
    cells = [p for tr in tours for p in tr]
    farm = Farm(seed, cells)
    valid = lambda c: c[0] == 0 and c[1] not in farm.cells
    def drone(i, tour):
        t = yield
        main = i == 0
        pos = (0, 0)
        while True:
            for p in tour:
                t = yield t + dist(pos, p) * ACT
                pos = p
                if farm.cells[p].alive:
                    r = farm.ready_at(p, t)
                    t = yield from water_wait(farm, p, t, W, RES)
                    farm.harvest(p, t); t = yield t + ACT
                    if main and farm.wood >= GOAL:
                        farm.end = t + ACT; return
                t = yield from plant_ok(farm, p, t, valid)
                c = farm.cells[p]
                if farm.end is not None and t >= farm.end: return
    return farm, [(i * ACT, drone(i, tr)) for i, tr in enumerate(tours)]


if __name__ == "__main__":
    W = float(sys.argv[1])
    f = run(make12, seed=0, W=W)
    print("W", W, round(f.end / TPS, 1), "water", f.water_used, "tank", f.tank(f.end))
