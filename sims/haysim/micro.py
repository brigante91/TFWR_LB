"""Confronto tick-esatto: script utente (vertical snake + dict + clear) vs versione micro."""
import math, statistics, sys
from haysim import Cell, ACT, YIELD, GOAL, S, TPS, WATER_DT, run
from strat import dist

class Done(Exception): pass

def origin(b):
    i = b % 8; bx = 4 * i; by = (8 * (b // 8) + 4 * (i % 2)) % S
    return i, bx, by

def setup_cost(b):
    i, bx, by = origin(b)
    ex = bx if i < 4 else bx + 3
    entry = (ex, by) if by <= 12 else (ex, (by + 7) % S)
    moves = dist((0, 0), entry) + (30 if by <= 12 else 31)
    goto_code = dist((0, 0), entry) + 12
    return 1000 + moves * ACT + 30 * ACT + goto_code, (bx + (2 if i < 4 else 1), by), (bx + (1 if i < 4 else 2), by)

BUILD = 2 * (24 * 16 + 6)      # costruzione dei due dizionari

OUT = {'on': 0}
def wait_water(farm, cell, t, W, spin_w, spin_ok, WN1=1, FERT=0):
    if OUT['on'] and W > 0:
        t += 3
        if cell.w < W and farm.tank(t) > 0:
            farm.water_used += 1; cell.update(t); cell.w = min(1.0, cell.w + 0.25)
            t = yield t + ACT
        t += 1
        while True:
            r = cell.ready_at(t)
            if r <= t:
                return t
            t = yield t + max(1, math.ceil(r - t))
    """while not can_harvest(): if get_water()<W [and tank>0]: use_item(WATER)"""
    t += 2
    while True:
        r = cell.ready_at(t)
        if r <= t:
            return t
        if FERT:
            t += 3
            if r - t > FERT and int(t / (TPS * 1.25)) - farm.fert_used > 0:
                farm.fert_used += 1; cell.update(t); cell.prog = 1.0
                t = yield t + ACT; continue
        if cell.w < W:
            if farm.tank(t) >= WN1:
                farm.water_used += WN1; cell.update(t); cell.w = min(1.0, cell.w + 0.25 * WN1)
                t = yield t + spin_w + ACT; continue
            t = yield t + spin_w + 1; continue
        t = yield t + max(spin_ok, math.ceil((r - t) / spin_ok) * spin_ok)

def reroll(farm, cell, pos, other, t, main, first_check=5, check=4, goalchk=0):
    # harvest() then while companion not ok: harvest()
    nchk = 0
    while True:
        cell.update(t)
        if cell.prog >= 1 and cell.comp is not None and cell.comp[0] == 0 and cell.comp[1] in farm.bush:
            farm.hay += YIELD
        elif cell.prog < 1 and nchk == 0:
            farm.unripe += 1
        cell.prog = 0.0; cell.t = t; cell.comp = farm.roll(pos)
        t = yield t + ACT + goalchk
        if main and goalchk and farm.hay >= GOAL:
            farm.end = t + ACT; raise Done
        if farm.end is not None and t >= farm.end: raise Done
        t += first_check if nchk == 0 else check
        nchk += 1
        if cell.comp[0] == 0 and cell.comp[1] != other:
            return t

def drone_old(farm, b, W=0.7, W0=0.4, EARLY=7):
    t = yield
    main = b == 0
    t0, A, C = setup_cost(b)
    t = yield t0 + BUILD
    ca = farm.grass.setdefault(A, Cell()); cc = farm.grass.setdefault(C, Cell())
    sw = 7; so = 4    # spin: con acqua / senza
    k = 0
    try:
        while True:
            w = W0 if k < EARLY else W
            gc = 3 if (main and k >= EARLY) else 0
            t = yield from wait_water(farm, ca, t, w, sw, so)
            t = yield from reroll(farm, ca, A, C, t, main, goalchk=gc)
            t = yield t + ACT
            t = yield from wait_water(farm, cc, t, w, sw, so)
            t = yield from reroll(farm, cc, C, A, t, main, goalchk=gc)
            t = yield t + ACT
            k += 1
    except Done:
        return

def drone_new(farm, b, W=0.7, W0=0.4, EARLY=7, WR=0.9, K=8, THR=64, NEAR=50_000_000, WN=1, WN1=1, FERT=0, WC=0, OUTW=0, A2=0):
    t = yield
    OUT['on'] = OUTW
    main = b == 0
    t0, A, C = setup_cost(b)
    t = yield t0                                  # dizionari costruiti dopo, durante l'attesa
    ca = farm.grass.setdefault(A, Cell()); cc = farm.grass.setdefault(C, Cell())
    sw = 4; so = 3
    try:
        # primo ciclo: controllo economico senza dizionari (tipo 3 + posizione 5 sui bush)
        t = yield from wait_water(farm, ca, t, W0, sw, so)
        t = yield from reroll(farm, ca, A, C, t, main, first_check=4, check=4.6)
        t = yield t + ACT
        t = yield from wait_water(farm, cc, t, W0, sw, so)
        t = yield from reroll(farm, cc, C, A, t, main, first_check=4, check=4.6)
        if WC and farm.tank(t) > 0:
            farm.water_used += 1; cc.update(t); cc.w = min(1.0, cc.w + 0.25); t = yield t + ACT
        t = yield t + ACT
        # ritorno su A: acqua, poi costruzione dei dizionari (sovrapposta alla crescita)
        if A2:
            if farm.tank(t) >= A2:
                farm.water_used += A2; ca.update(t); ca.w = min(1.0, ca.w + 0.25 * A2); t = yield t + ACT
            else:
                t += 1
        for _ in range(0 if A2 else 2):
            t += 3
            if ca.w < W0 and farm.tank(t) > 0:
                farm.water_used += 1; ca.update(t); ca.w = min(1.0, ca.w + 0.25); t = yield t + ACT
        t = yield t + BUILD
        k = 1
        # fase 1
        while True:
            w = W0 if k < EARLY else W
            t = yield from wait_water(farm, ca, t, w, sw, so, WN1, FERT)
            t = yield from reroll(farm, ca, A, C, t, main)
            t = yield t + ACT
            t = yield from wait_water(farm, cc, t, w, sw, so, WN1, FERT)
            t = yield from reroll(farm, cc, C, A, t, main)
            t = yield t + ACT
            k += 1
            t += 3
            if farm.tank(t) > THR:
                farm.p2.append(t / TPS)
                break
        # fase 2: niente can_harvest, acqua ogni K cicli
        first = True
        while True:
            if main:
                t += 2
                if farm.hay >= GOAL - NEAR:
                    break
            for cyc in range(K):
                for cell, pos, oth in ((ca, A, C), (cc, C, A)):
                    if cyc == 0:
                        while True:
                            t += 3
                            if cell.w >= WR: break
                            if farm.tank(t) >= WN:
                                farm.water_used += WN; cell.update(t); cell.w = min(1.0, cell.w + 0.25 * WN); t = yield t + ACT
                            else:
                                farm.spin += 1
                                t = yield t + 1
                        if first:
                            t = yield from wait_water(farm, cell, t, 0, sw, so)
                    t = yield from reroll(farm, cell, pos, oth, t, main)
                    t = yield t + ACT
                first = False
        # finale (solo principale): controllo dopo ogni azione
        while True:
            for cell, pos, oth in ((ca, A, C), (cc, C, A)):
                t = yield from reroll(farm, cell, pos, oth, t, main, goalchk=3)
                t = yield t + ACT + 3
                if farm.hay >= GOAL:
                    farm.end = t + ACT; raise Done
    except Done:
        return

def make(drone, **kw):
    def strat(farm):
        farm.end = None; farm.unripe = 0
        st = {}
        return [(0, drone(farm, b, **kw)) for b in range(32)]
    return strat

def bushes():
    s = set()
    for b in range(32):
        i, bx, by = origin(b)
        for dx in range(4):
            for dy in range(8):
                s.add(((bx + dx) % S, (by + dy) % S))
    for b in range(32):
        i, bx, by = origin(b)
        s.discard((bx + 1, by)); s.discard((bx + 2, by))
    return s

def ev(drone, n, **kw):
    out = []; unr = 0
    B = bushes()
    for s in range(n):
        def strat(farm, kw=kw):
            farm.end = None; farm.unripe = 0; farm.bush = B; farm.p2 = []; farm.spin = 0; farm.fert_used = 0
            return [(0, drone(farm, b, **kw)) for b in range(32)]
        f = run(strat, seed=s)[1]
        out.append(f.end / TPS); unr += f.unripe
        if f.p2: print('  fase2 da %.1f a %.1f s, spin %d, acqua usata %d, tank finale %d' % (min(f.p2), max(f.p2), f.spin, f.water_used, f.tank(f.end)))
    return statistics.mean(out), unr / n

if __name__ == "__main__":
    which = sys.argv[1]; n = int(sys.argv[2])
    kw = {a.split("=")[0]: float(a.split("=")[1]) for a in sys.argv[3:]}
    for k in ("EARLY", "K", "THR"):
        if k in kw: kw[k] = int(kw[k])
    d = drone_old if which == "old" else drone_new
    m, u = ev(d, n, **kw)
    print(which, kw, "media %.3f s" % m, "unripe/run %.1f" % u)
