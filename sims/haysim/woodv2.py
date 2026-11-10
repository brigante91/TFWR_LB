"""Varianti per lb_wood_v2: stesso modello di woodsim (Farm), strategie nuove.

Layout "linee": alberi su tutte le celle con (x - y) % 4 == 0 (8 diagonali da 32 celle,
256 alberi). Ogni albero ha ESATTAMENTE 2 alberi nel rombo r=3 (i vicini sulla diagonale):
companion valido 22/72 = 0.306. 4 droni per diagonale che girano nello stesso verso
(convoglio): 2 mosse per albero, nessun ritorno.
Layout "ladder": coppie di diagonali (c, c+4), 4+4 alberi per drone, 2.5 mosse/albero.
"""
import sys, os, math, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from woodsim import Farm, run, ACT, TPS, GOAL, YIELD, WATER_DT, S
from wood12 import make12

NH = GOAL // YIELD + (1 if GOAL % YIELD else 0)   # 24415 raccolti


def dist(a, b):
    dx = (b[0] - a[0]) % S; dy = (b[1] - a[1]) % S
    return min(dx, S - dx) + min(dy, S - dy)


class Stats:
    def __init__(self):
        self.wait = 0; self.water = 0; self.rerolls = 0; self.harv = 0; self.moves = 0
        self.extra_harv = 0; self.zero = 0; self.waits = 0


def water_tree(farm, c, n):
    farm.water_used += n; c.w = min(1.0, c.w + 0.25 * n)


def wait_ready(farm, st, p, t, W, WN, RES, ENDED):
    """while not can_harvest(): if get_water() < W and num_items(Water) >= WN: use_item(Water, WN)"""
    first = True
    while True:
        r = farm.ready_at(p, t)
        if r <= t:
            return t
        if ENDED():
            return t
        c = farm.cells[p]
        if c.w < W and farm.tank(t) >= WN + RES:
            water_tree(farm, c, WN); st.water += 1
            t = yield t + ACT
            continue
        if c.w < W:
            nxt = (math.floor(t / WATER_DT) + 1) * WATER_DT
            r = min(r, nxt)
        if first:
            st.waits += 1; first = False
        d = max(6, math.ceil((r - t) / 6) * 6)
        st.wait += d
        t = yield t + d


def plant_ok(farm, st, p, t, valid):
    while True:
        comp = farm.plant(p, t)
        t = yield t + ACT + 5
        if valid(comp):
            return t
        st.rerolls += 1
        farm.harvest(p, t)
        t = yield t + ACT + 1


def lines_cells():
    return [(x, y) for x in range(S) for y in range(S) if (x - y) % 4 == 0]


def make_lines(seed, W=0.9, WN=1, RES=0, WPOL=0, EX=0, T1=0.0, ENDK=0, GATE=40, PW=0,
               SPAWN="tree", EXP=1.0, ANY=1, STAG=0):
    """Convoglio su 8 diagonali, 4 droni per diagonale.
    W/WN/RES: soglia acqua, unita' per use_item, riserva serbatoio.
    WPOL: 0 = annaffia solo durante le attese; 1 = anche al raccolto se acqua < W.
    EX: passo degli alberi extra (0 = niente; 1 = uno per ogni albero del segmento iniziale,
        2 = uno ogni due...) sulla diagonale c+2, raccolti/ripiantati solo dal drone che li ha
        piantati finche' get_time() < T1, poi rimossi.
    ENDK: a fine partita (legno >= GOAL - ENDK*YIELD) i droni raccolgono senza ripiantare.
    GATE: i droni controllano num_items solo quando il proprio conteggio >= NH/32 - GATE.
    PW: alla piantagione, se il serbatoio ha >= PW unita', use_item(Water, PW) subito.
    ANY: 1 = qualunque drone che vede l'obiettivo chiude con clear(); 0 = solo il main.
    """
    st = Stats()
    mains = lines_cells()
    mainset = set(mains)
    extras = {}   # drone -> lista celle extra
    allcells = list(mains)
    L = {}
    for c in range(0, S, 4):
        L[c] = [((y + c) % S, y) for y in range(S)]
    drones = []
    for li, c in enumerate(range(0, S, 4)):
        for j in range(4):
            drones.append((c, j))
    ex_cells = set()
    if EX:
        for (c, j) in drones:
            lst = []
            for i in range(0, 8, EX):
                y = 8 * j + i
                q = ((y + c + 1) % S, (y - 1) % S)
                lst.append(q)
                ex_cells.add(q)
            extras[(c, j)] = lst
        allcells += sorted(ex_cells)
    farm = Farm(seed, allcells)
    farm.st = st
    T1t = T1 * TPS
    per_drone = NH // 32

    def valid_late(comp):
        return comp[0] == 0 and comp[1] not in mainset

    def valid_early(comp):
        return comp[0] == 0 and comp[1] not in mainset and comp[1] not in ex_cells

    def ENDED():
        return farm.end is not None

    def drone(di, c, j, spawn_t):
        t = yield
        line = L[c]
        start = 8 * j
        myex = extras.get((c, j), [])
        exidx = {}
        for i, q in enumerate(myex):
            exidx[(start + i * EX) % S] = q
        pos = (0, 0)
        d = dist(pos, line[start])
        t = yield t + d * ACT
        st.moves += d
        idx = start
        cnt = 0
        endmode = False
        ex_alive = {}
        ex_done = len(myex) == 0
        main = di == 0
        lap = 0
        while True:
            if farm.end is not None:
                return
            p = line[idx]
            cell = farm.cells[p]
            # --- cella principale
            if cell.alive:
                if WPOL == 1 and cell.w < W and farm.tank(t) >= WN + RES and not endmode:
                    water_tree(farm, cell, WN); st.water += 1
                    t = yield t + ACT
                t = yield from wait_ready(farm, st, p, t, W, WN, RES, ENDED)
                if farm.end is not None:
                    return
                if cell.alive:
                    ok = farm.comp_ok(cell.comp)
                    farm.harvest(p, t)
                    t = yield t + ACT
                    st.harv += 1
                    if not ok:
                        st.zero += 1
                    cnt += 1
                    if (ANY or main) and cnt >= per_drone - GATE:
                        t += 2
                        if farm.wood >= GOAL:
                            farm.end = t + ACT
                            return
                        if ENDK and farm.wood >= GOAL - ENDK * YIELD:
                            endmode = True
            if not endmode:
                early = EX and t < T1t
                t = yield from plant_ok(farm, st, p, t, valid_early if early else valid_late)
                if PW and farm.tank(t) >= PW and farm.cells[p].w < 1.0 - 0.25 * PW + 1e-9:
                    water_tree(farm, farm.cells[p], PW); st.water += 1
                    t = yield t + ACT
            # --- albero extra proprio (diagonale c+2), solo nella fase iniziale
            if not ex_done and idx in exidx:
                q = exidx[idx]
                ec = farm.cells[q]
                if t < T1t:
                    if not ec.alive:
                        t = yield t + 2 * ACT; st.moves += 2
                        t = yield from plant_ok(farm, st, q, t, valid_early)
                        ex_alive[q] = True
                        t = yield t + 2 * ACT; st.moves += 2
                        idx = (idx + 1) % S
                        continue
                    elif farm.ready_at(q, t) <= t:
                        t = yield t + 2 * ACT; st.moves += 2
                        ok = farm.comp_ok(ec.comp)
                        farm.harvest(q, t); t = yield t + ACT
                        st.harv += 1; st.extra_harv += 1; cnt += 1
                        if not ok:
                            st.zero += 1
                        t = yield from plant_ok(farm, st, q, t, valid_early)
                        t = yield t + 2 * ACT; st.moves += 2
                        idx = (idx + 1) % S
                        continue
                else:
                    if ec.alive:
                        t = yield t + 2 * ACT; st.moves += 2
                        ok = farm.comp_ok(ec.comp) and farm.ready_at(q, t) <= t
                        farm.harvest(q, t); t = yield t + ACT
                        if ok:
                            st.harv += 1; st.extra_harv += 1; cnt += 1
                        ex_alive.pop(q, None)
                        if not ex_alive:
                            ex_done = True
                        t = yield t + 2 * ACT; st.moves += 2
                        idx = (idx + 1) % S
                        continue
                    else:
                        ex_alive.pop(q, None)
                        if not ex_alive:
                            ex_done = True
            t = yield t + 2 * ACT + 4
            st.moves += 2
            idx = (idx + 1) % S

    gens = []
    for di, (c, j) in enumerate(drones):
        if SPAWN == "tree":
            k = di.bit_length()   # livello nell'albero binario degli spawn
            t0 = (k + 1) * ACT if di else 0
            # il drone che spawna paga 200 per ogni figlio: il figlio i parte dopo (livello) azioni
            t0 = k * ACT
        else:
            t0 = di * ACT
        gens.append((t0, drone(di, c, j, t0)))
    return farm, gens


def ev(make, n=5, seeds=None, **kw):
    out = []
    for s in (seeds or range(n)):
        f = run(make, seed=s, **kw)
        out.append(f.end / TPS)
    return statistics.mean(out), out


def report(name, make, n=5, **kw):
    m, out = ev(make, n, **kw)
    f = run(make, seed=0, **kw)
    extra = ""
    if hasattr(f, "st"):
        st = f.st
        extra = " harv %d extra %d zero %d reroll %d water %d wait %.1fs(%d) moves %d" % (
            st.harv, st.extra_harv, st.zero, st.rerolls, st.water, st.wait / TPS / 32, st.waits, st.moves)
    print("%-40s %7.2f  %s%s" % (name, m, " ".join("%.1f" % x for x in out), extra))
    return m


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "base":
        report("wood12 W=0.9 (base)", make12, W=0.9)
    else:
        kw = dict(a.split("=") for a in sys.argv[1:])
        kw = {k: (float(v) if "." in v else int(v)) for k, v in kw.items()}
        report("lines " + str(kw), make_lines, **kw)


def ladder_tours():
    tours = []
    for c in range(0, S, 8):
        for j in range(8):
            A = [((4 * j + i + c) % S, 4 * j + i) for i in range(4)]
            B = [((4 * j + i + c + 4) % S, 4 * j + i) for i in reversed(range(4))]
            tours.append(A + B)
    return tours


def make_tours(seed, tours=None, W=0.9, WN=1, RES=0, WPOL=0, ENDK=0, GATE=40, PW=0, ANY=1):
    """Droni indipendenti su anelli fissi (ladder diagonale: 8 alberi, 20 mosse)."""
    st = Stats()
    tours = tours or ladder_tours()
    cells = [p for tr in tours for p in tr]
    cellset = set(cells)
    farm = Farm(seed, cells)
    farm.st = st
    per_drone = NH // 32
    valid = lambda comp: comp[0] == 0 and comp[1] not in cellset

    def ENDED():
        return farm.end is not None

    def drone(di, tour):
        t = yield
        pos = (0, 0)
        cnt = 0; endmode = False
        main = di == 0
        n = len(tour)
        while True:
            for k in range(n):
                p = tour[k]
                d = dist(pos, p); pos = p
                t = yield t + d * ACT + 4
                st.moves += d
                if farm.end is not None:
                    return
                cell = farm.cells[p]
                if cell.alive:
                    if WPOL == 1 and cell.w < W and farm.tank(t) >= WN + RES and not endmode:
                        water_tree(farm, cell, WN); st.water += 1
                        t = yield t + ACT
                    t = yield from wait_ready(farm, st, p, t, W, WN, RES, ENDED)
                    if farm.end is not None:
                        return
                    ok = farm.comp_ok(cell.comp)
                    farm.harvest(p, t); t = yield t + ACT
                    st.harv += 1; cnt += 1
                    if not ok: st.zero += 1
                    if (ANY or main) and cnt >= per_drone - GATE:
                        t += 2
                        if farm.wood >= GOAL:
                            farm.end = t + ACT; return
                        if ENDK and farm.wood >= GOAL - ENDK * YIELD:
                            endmode = True
                if not endmode:
                    t = yield from plant_ok(farm, st, p, t, valid)
                    if PW and farm.tank(t) >= PW and farm.cells[p].w < 1.0 - 0.25 * PW + 1e-9:
                        water_tree(farm, farm.cells[p], PW); st.water += 1
                        t = yield t + ACT
    gens = []
    for di, tr in enumerate(tours):
        gens.append((di.bit_length() * ACT, drone(di, tr)))
    return farm, gens


def ladder2_tours(EXN=0):
    """Ladder diagonale con alberi extra: E1 ed E2 a costo zero di mosse (sulla diagonale c+2,
    attraversate nei due tratti da 4 mosse), F3..F1 sulla diagonale c+6 (+2 mosse ciascuno).
    Ritorna per ogni drone la lista di (cella, is_extra)."""
    tours = []
    for c in range(0, S, 8):
        for j in range(8):
            x, y = (4 * j + c) % S, 4 * j
            def P(dx, dy):
                return ((x + dx) % S, (y + dy) % S)
            tr = [(P(i, i), 0) for i in range(4)]
            if EXN >= 1:
                tr.append((P(5, 3), 1))
            for i in reversed(range(4)):
                tr.append((P(4 + i, i), 0))
                if EXN >= 3 and i >= 1 and (i >= 5 - EXN):
                    tr.append((P(5 + i - 1, i - 2), 1))   # F_{i-1} = (x+5+(i-1), y+(i-1)-1)
            if EXN >= 2:
                tr.append((P(2, 0), 1))
            tours.append(tr)
    return tours


def make_ladder2(seed, EXN=0, T1=20.0, T2=None, W=0.8, WN=1, RES=0, WPOL=1, ENDK=0, GATE=40,
                 PW=0, ANY=1, EXW=0):
    st = Stats()
    tours = ladder2_tours(EXN)
    mains = [p for tr in tours for (p, e) in tr if not e]
    extras = [p for tr in tours for (p, e) in tr if e]
    mainset = set(mains); exset = set(extras)
    assert len(mainset) == 256 and len(exset) == len(extras), (len(mainset), len(exset), len(extras))
    for q in extras:
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = ((q[0] + d[0]) % S, (q[1] + d[1]) % S)
            assert n not in mainset and n not in exset, (q, n)
    farm = Farm(seed, mains + extras)
    farm.st = st
    per_drone = NH // 32
    T1t = T1 * TPS
    T2t = (T2 if T2 is not None else T1 + 10) * TPS
    valid_late = lambda comp: comp[0] == 0 and comp[1] not in mainset
    valid_early = lambda comp: comp[0] == 0 and comp[1] not in mainset and comp[1] not in exset

    def ENDED():
        return farm.end is not None

    def drone(di, tour):
        t = yield
        pos = (0, 0)
        cnt = 0; endmode = False
        main = di == 0
        full = tour
        pure = [(p, e) for (p, e) in tour if not e]
        cur = full if EXN else pure
        ex_alive = {}
        ex_done = EXN == 0
        while True:
            for (p, e) in cur:
                d = dist(pos, p); pos = p
                t = yield t + d * ACT + 4
                st.moves += d
                if farm.end is not None:
                    return
                cell = farm.cells[p]
                if e:
                    # albero extra: non annaffiato (EXW=0), raccolto se maturo
                    if cell.alive:
                        if farm.ready_at(p, t) <= t:
                            ok = farm.comp_ok(cell.comp)
                            farm.harvest(p, t); t = yield t + ACT
                            st.harv += 1; st.extra_harv += 1; cnt += 1
                            if not ok: st.zero += 1
                            if t < T1t:
                                t = yield from plant_ok(farm, st, p, t, valid_early)
                            else:
                                ex_alive.pop(p, None)
                        else:
                            if EXW and cell.w < EXW and farm.tank(t) >= WN + RES:
                                water_tree(farm, cell, WN); st.water += 1
                                t = yield t + ACT
                            t += 2
                    else:
                        if t < T1t:
                            t = yield from plant_ok(farm, st, p, t, valid_early)
                            ex_alive[p] = True
                        else:
                            ex_alive.pop(p, None)
                    if t >= T1t and not ex_alive:
                        ex_done = True
                    continue
                if cell.alive:
                    if WPOL == 1 and cell.w < W and farm.tank(t) >= WN + RES and not endmode:
                        water_tree(farm, cell, WN); st.water += 1
                        t = yield t + ACT
                    t = yield from wait_ready(farm, st, p, t, W, WN, RES, ENDED)
                    if farm.end is not None:
                        return
                    ok = farm.comp_ok(cell.comp)
                    farm.harvest(p, t); t = yield t + ACT
                    st.harv += 1; cnt += 1
                    if not ok: st.zero += 1
                    if (ANY or main) and cnt >= per_drone - GATE:
                        t += 2
                        if farm.wood >= GOAL:
                            farm.end = t + ACT; return
                        if ENDK and farm.wood >= GOAL - ENDK * YIELD:
                            endmode = True
                if not endmode:
                    t = yield from plant_ok(farm, st, p, t, valid_early if t < T2t else valid_late)
                    if PW and farm.tank(t) >= PW and farm.cells[p].w < 1.0 - 0.25 * PW + 1e-9:
                        water_tree(farm, farm.cells[p], PW); st.water += 1
                        t = yield t + ACT
            if ex_done:
                cur = pure
    gens = []
    for di, tr in enumerate(tours):
        gens.append((di.bit_length() * ACT, drone(di, tr)))
    return farm, gens
