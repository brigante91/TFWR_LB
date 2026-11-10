# Single: varianti della v1 per ridurre il sovraccarico.
# HR=1: la pianta col secondo fiore sbagliato si tiene fino al taglio (rende (f2-1)^2) e si ripianta li'.
# EMIN: ripianta (sempre al taglio, dopo aver raccolto) se F - f2 < EMIN.
# Percorso: rettangolo W x R (R pari) con ritorno lungo x=0, (0,0) vuota.
import random, sys, statistics
from sim import Sim, ACT, OP

def loop(W, R):
    p = [(x, 0) for x in range(W)]
    for y in range(1, R):
        xs = range(W - 1, 0, -1) if y % 2 == 1 else range(1, W)
        p += [(x, y) for x in xs]
    p += [(0, y) for y in range(R - 1, 0, -1)]
    return [y * 8 + x for x, y in p]

def run(T1=5, D=4, W=8, R=6, WS=1.0, WT=1.0, WLOW=0.5, MARGIN=0.05, HR=1, DLO=0, DHI=0, EMIN=0, EMIN_R1=0, seed=1, goal=2.5e7, tmax=900):
    rng = random.Random(seed)
    path = loop(W, R); n = len(path)
    sim = Sim(64, rng, 25.6)
    T2 = T1 + D; M1 = T1 - 1; M2 = T2 - 1
    sim.pos = path[0]
    cnt = {"setup": 0, "reroll": 0, "water": 0, "sweep": 0}
    bad = [False] * n

    def water_to(tgt, low):
        w = sim.get_water()
        if w < low and sim.tank() >= 1:
            k = max(1, int((tgt - w) * 4))
            sim.water(k); cnt["water"] += 1

    def new_plant():
        sim.plant()
        while sim.measure() != M1:
            sim.harvest(); sim.plant()

    a0 = sim.nact
    for k in range(1, n):
        sim.move_to(path[k])
        if not sim.cur().soil:
            sim.till()
        new_plant()
        water_to(WS, WS)
    sim.move_to(path[0])
    cnt["setup"] = sim.nact - a0
    prev_end = sim.t
    wmin = 0.0
    need1 = M1
    sweep = (n - 1) * (ACT + 3 * OP)

    def guard(blocks):
        sim.wait_until(prev_end + blocks / (1 + 4 * wmin) + MARGIN - sweep)

    while sim.t < tmax:
        guard(need1)
        sim.hover(M1)
        for k in range(1, n):
            sim.move_to(path[k])
            m = sim.measure()
            dd = m - M1
            if m != M2 and m != M1 and not (DLO and DLO <= dd <= DHI):
                if HR:
                    bad[k] = True
                else:
                    a = sim.nact
                    sim.harvest(); new_plant(); sim.hover(M1)
                    cnt["reroll"] += sim.nact - a; sim.stats["reroll"] += 1
        sim.move_to(path[0]); prev_end = sim.t
        guard(D)
        sim.hover(M2)
        emax = 3
        for k in range(1, n):
            sim.move_to(path[k])
            mm = sim.measure()
            if mm is not None and mm > M2:
                e = mm - M2
                if e > emax: emax = e
                lim = EMIN_R1 if sim.cur().r else EMIN
                if lim and e < lim:
                    bad[k] = True
        if emax > 5: emax = 5
        sim.move_to(path[0]); prev_end = sim.t
        guard(emax)
        sim.hover(1)
        wm = 1.0
        rer = False
        for k in range(1, n):
            sim.move_to(path[k])
            if sim.bamboo >= goal:
                sim.cnt = cnt; return sim
            if bad[k]:
                a = sim.nact
                sim.harvest(); new_plant()
                cnt["reroll"] += sim.nact - a; sim.stats["reroll"] += 1
                bad[k] = False; rer = True
            water_to(WT, WLOW)
            w = sim.cur().water_at(sim.t)
            if w < wm: wm = w
        need1 = M1 if rer else T1 - 2
        sim.move_to(path[0]); prev_end = sim.t
        wmin = wm * 0.97
    sim.cnt = cnt
    return sim

if __name__ == "__main__":
    kw = {}
    for a in sys.argv[1:]:
        k, v = a.split("="); kw[k] = float(v) if "." in v else int(v)
    N = kw.pop("N", 8)
    res = []; tot = {}
    for s in range(N):
        sim = run(seed=s, **kw)
        res.append(sim.t)
        for k, v in sim.cnt.items(): tot[k] = tot.get(k, 0) + v / N
        tot["act"] = tot.get("act", 0) + sim.nact / N
        tot["wait"] = tot.get("wait", 0) + sim.stats["wait"] / N
        tot["nrr"] = tot.get("nrr", 0) + sim.stats["reroll"] / N
    print(kw, "t=%.1f +- %.1f" % (statistics.mean(res), statistics.pstdev(res)), {k: round(v, 1) for k, v in tot.items()})
