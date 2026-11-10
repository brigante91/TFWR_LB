import sys, math
from woodsim import *
from woodstrat import dist
from wood12 import tours12
FERT_DT = TPS * 20 / 16


def make(seed, W=0.9, RES=0, FERT=0, SKIP=0):
    tours = tours12()
    cells = [p for tr in tours for p in tr]
    farm = Farm(seed, cells)
    farm.fert_used = 0
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
                    if SKIP and r - t > SKIP:
                        continue
                    if FERT and r - t > FERT and int(t / FERT_DT) - farm.fert_used > 0:
                        farm.fert_used += 1
                        c = farm.update(p, t)
                        c.prog = min(1.0, c.prog + 2 * TPS / c.dur)  # +2 s di crescita base
                        t = yield t + ACT
                    t = yield from water_wait(farm, p, t, W, RES)
                    farm.harvest(p, t); t = yield t + ACT
                    if main and farm.wood >= GOAL:
                        farm.end = t + ACT; return
                t = yield from plant_ok(farm, p, t, valid)
                if farm.end is not None and t >= farm.end: return
    return farm, [(i * ACT, drone(i, tr)) for i, tr in enumerate(tours)]


if __name__ == "__main__":
    kw = dict(a.split("=") for a in sys.argv[1:])
    kw = {k: float(v) for k, v in kw.items()}
    f = run(make, seed=0, **kw)
    print(kw, round(f.end / TPS, 1), "fert", f.fert_used)
