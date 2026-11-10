# Strategia v1: passate a quota costante su un percorso chiuso con una cella "ascensore" vuota.
# Ogni pianta viene ritirata finche' f1 == T1 (subito con measure) e f2 - f1 == D (dopo la prima raccolta del fiore).
import random, sys
from sim import Sim, ACT, OP

def band(S, R):
    # ciclo hamiltoniano su R righe (R pari): riga 0 verso est, righe 1..R-1 a serpentina su x>=1, ritorno lungo x=0
    if R == S:
        return snake(S)
    p = [x for x in range(S)]
    for y in range(1, R):
        xs = range(S - 1, 0, -1) if y % 2 == 1 else range(1, S)
        for x in xs:
            p.append(y * S + x)
    for y in range(R - 1, 0, -1):
        p.append(y * S)
    return p

def snake(S):
    p = []
    for y in range(S):
        xs = range(S) if y % 2 == 0 else range(S - 1, -1, -1)
        for x in xs:
            p.append(y * S + x)
    return p

def run(S, rows, tank_rate, goal, T1=5, D=4, WT=0.5, WS=0.5, MARGIN=0.05, EMIN=0, WSTEP=4, WRISE=9.0, R=8, WLOW=9.0, seed=1, tmax=600):
    rng = random.Random(seed)
    if rows == 1:   # single: serpentina chiusa sul campo SxS
        path = band(S, R); n = len(path)
        sim = Sim(S * S, rng, tank_rate)
    else:           # multi: una riga per drone (giro con wrap)
        path = list(range(S)); n = S
        sim = Sim(S, rng, tank_rate)
    T2 = T1 + D
    sim.pos = path[0]

    def water_to(target, low=None):
        w = sim.get_water()
        if w < (target if low is None else low):
            k = min(WSTEP, int((target - w) * 4 + 0.999))
            if sim.tank() >= 1:
                sim.water(k)

    def reroll():
        sim.stats["reroll"] += 1
        sim.harvest(); sim.plant()
        while sim.measure() != T1 - 1:
            sim.harvest(); sim.plant()

    # semina
    for k in range(n):
        if not sim.cur().soil:
            sim.till()
        if k != 0:
            sim.plant()
            while sim.measure() != T1 - 1:
                sim.harvest(); sim.plant()
            water_to(WS)
        sim.move_to(path[(k + 1) % n])
    prev_end = sim.t
    wmin = 0.0
    first = True
    sweep = (n - 1) * (ACT + 3 * OP)

    def guard(blocks):
        need = blocks / (1 + 4 * wmin) + MARGIN
        sim.wait_until(prev_end + need - sweep)

    while sim.t < tmax:
        # raccolta del primo fiore (quota T1-1)
        guard(T1 - 1 if first else T1 - 2)
        first = False
        sim.hover(T1 - 1)
        for k in range(1, n):
            sim.move_to(path[k])
            m = sim.measure()
            if m == T2 - 1:
                pass
            elif m == T1 - 1:
                sim.stats["pluck_miss"] += 1
            else:
                reroll(); sim.hover(T1 - 1)
        sim.move_to(path[0]); prev_end = sim.t
        # secondo fiore (quota T2-1)
        guard(D)
        sim.hover(T2 - 1)
        emax = 3
        for k in range(1, n):
            sim.move_to(path[k])
            mm = sim.measure()
            if mm is not None and mm >= T2 and mm - (T2 - 1) > emax: emax = mm - (T2 - 1)
            if EMIN:
                m = sim.measure()
                if m is not None and m > T2 and m - (T2 - 1) < EMIN:
                    reroll(); sim.hover(T2 - 1)
        sim.move_to(path[0]); prev_end = sim.t
        # taglio a quota 1
        guard(emax)
        sim.hover(1)
        wm = 1.0
        tgt = min(WT, wmin / 0.97 + WRISE)
        for k in range(1, n):
            sim.move_to(path[k])
            water_to(tgt, min(tgt, WLOW))
            w = sim.cur().water_at(sim.t)
            if w < wm: wm = w
            if sim.bamboo >= goal:
                return sim
        sim.move_to(path[0]); prev_end = sim.t
        wmin = wm * 0.97
    return sim

if __name__ == "__main__":
    import statistics
    kw = {}
    for a in sys.argv[1:]:
        k, v = a.split("="); kw[k] = float(v) if "." in v else int(v)
    mode = kw.pop("mode", 1)
    N = kw.pop("N", 8)
    res = []
    for s in range(N):
        if mode == 1:
            sim = run(8, 1, 25.6, 2.5e7, seed=s, **kw)
        else:
            sim = run(32, 32, 0.8, 5e8 / 32, seed=s, **kw)
        res.append(sim.t)
    print("mode", mode, kw, "t=%.1f +- %.1f" % (statistics.mean(res), statistics.pstdev(res)),
          "reroll", sim.stats["reroll"], "miss", sim.stats["pluck_miss"], "wait %.1f" % sim.stats["wait"], "act", sim.nact)
