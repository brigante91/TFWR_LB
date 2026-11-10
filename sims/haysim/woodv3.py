"""Strategie generalizzate per lb_wood_v2 (stesso modello Farm di woodsim).

Layout: reticolo (x - y) % 4 == 0 (256 alberi, 2 alberi nel rombo r=3 -> companion valido 22/72).
Loop "ladder" con m alberi sulla diagonale c (y = y0..y0+m-1) e m sulla diagonale c+4 all'indietro:
2m alberi, 4m+4 mosse.  K droni per loop, equidistanti.  m=4,K=1 (indipendenti, 2.5 mosse/albero);
m=8,K=2 (2.25); m=16,K=4 (2.125); m=32 "conv" = diagonale intera, K=4 (2.0).
Acqua: soglia W; dose WN (0 = adattiva: porta a 1.0 con quante unita' ha il serbatoio);
W0 fino a T0 secondi (fase iniziale).
"""
import sys, os, math, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from woodsim import Farm, run, ACT, TPS, GOAL, YIELD, WATER_DT, S

NH = GOAL // YIELD + (1 if GOAL % YIELD else 0)


def dist(a, b):
    dx = (b[0] - a[0]) % S; dy = (b[1] - a[1]) % S
    return min(dx, S - dx) + min(dy, S - dy)


class Stats:
    def __init__(self):
        self.wait = 0; self.water = 0; self.rerolls = 0; self.harv = 0; self.moves = 0
        self.zero = 0; self.waits = 0; self.wait_hist = {}; self.extra_harv = 0


def loops_ladder(m):
    loops = []
    if m == 32:
        for c in range(0, S, 4):
            loops.append([((y + c) % S, y) for y in range(S)])
        return loops
    for c in range(0, S, 8):
        for y0 in range(0, S, m):
            A = [((y0 + i + c) % S, y0 + i) for i in range(m)]
            B = [((y0 + i + c + 4) % S, y0 + i) for i in reversed(range(m))]
            loops.append(A + B)
    return loops


def make(seed, m=4, W=0.9, WN=1, W0=None, T0=0.0, RES=0, GATE=40, OV_STEP=4, OV_PLANT=5,
         OV_RR=1, WAIT_Q=6, EXTRA=0, T1=0.0, PREW=0):
    """EXTRA: alberi extra per drone nella fase iniziale (t < T1 s) su celle libere non adiacenti
    e fuori dai rombi dei propri alberi dove possibile (diagonale c+2)."""
    st = Stats()
    loops = loops_ladder(m)
    K = 32 // len(loops)
    assert K * len(loops) == 32
    cells = [p for lp in loops for p in lp]
    cellset = set(cells)
    assert len(cellset) == 256
    # celle extra: diagonale c+2 fra le due diagonali del loop (dist 2 dagli alberi: dentro i rombi)
    extras = {}
    exset = set()
    if EXTRA:
        for li, lp in enumerate(loops):
            for k in range(K):
                lst = []
                base = (li, k)
                # alberi del drone: segmento di 2m/K alberi a partire da k*2m/K
                seg = lp[k * (2 * len(lp) // 2 // K):(k + 1) * (2 * len(lp) // 2 // K)]
                for i in range(0, len(seg), max(1, len(seg) // EXTRA)):
                    p = seg[i]
                    q = ((p[0] + 1) % S, (p[1] - 1) % S)   # diagonale c+2
                    if q not in cellset and q not in exset:
                        ok = True
                        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            n = ((q[0] + d[0]) % S, (q[1] + d[1]) % S)
                            if n in cellset or n in exset:
                                ok = False
                        if ok:
                            lst.append(q); exset.add(q)
                    if len(lst) >= EXTRA:
                        break
                extras[base] = lst
    farm = Farm(seed, cells + sorted(exset))
    farm.st = st
    per_drone = NH // 32
    T0t = T0 * TPS; T1t = T1 * TPS

    def valid(comp):
        return comp[0] == 0 and comp[1] not in cellset and not (comp[1] in exset and farm.cells[comp[1]].alive)

    def thr(t):
        return W0 if (W0 is not None and t < T0t) else W

    def dose(c, t):
        tk = farm.tank(t) - RES
        if tk <= 0:
            return 0
        if WN:
            return WN if tk >= WN else 0
        need = int(math.ceil((1.0 - c.w) / 0.25 - 1e-9))
        return max(0, min(need, tk))

    def water(c, n):
        farm.water_used += n; c.w = min(1.0, c.w + 0.25 * n); st.water += 1

    def wait_ready(p, t):
        first = True
        while True:
            r = farm.ready_at(p, t)
            if r <= t or farm.end is not None:
                return t
            c = farm.cells[p]
            Wt = thr(t)
            if c.w < Wt:
                n = dose(c, t)
                if n:
                    water(c, n)
                    t = yield t + ACT
                    continue
                nxt = (math.floor(t / WATER_DT) + 1) * WATER_DT
                r = min(r, nxt)
            if first:
                st.waits += 1; first = False
            d = max(WAIT_Q, math.ceil((r - t) / WAIT_Q) * WAIT_Q)
            st.wait += d
            b = int(t / TPS) // 10
            st.wait_hist[b] = st.wait_hist.get(b, 0) + d
            t = yield t + d

    def plant_ok(p, t):
        while True:
            comp = farm.plant(p, t)
            t = yield t + ACT + OV_PLANT
            if valid(comp):
                return t
            st.rerolls += 1
            farm.harvest(p, t)
            t = yield t + ACT + OV_RR

    def drone(di, lp, k):
        t = yield
        n = len(lp)
        start = k * (n // K)
        pos = (0, 0)
        cnt = 0
        myex = extras.get((di // K, k), []) if EXTRA else []
        exidx = {}
        seg = lp[start:start + n // K]
        for i, q in enumerate(myex):
            exidx[(start + i * max(1, len(seg) // EXTRA)) % n] = q
        ex_alive = set()
        idx = start
        while True:
            p = lp[idx]
            d = dist(pos, p); pos = p
            t = yield t + d * ACT + OV_STEP
            st.moves += d
            if farm.end is not None:
                return
            cell = farm.cells[p]
            if cell.alive:
                t = yield from wait_ready(p, t)
                if farm.end is not None:
                    return
                ok = farm.comp_ok(cell.comp)
                farm.harvest(p, t); t = yield t + ACT
                st.harv += 1; cnt += 1
                if not ok: st.zero += 1
                if cnt >= per_drone - GATE:
                    t += 2
                    if farm.wood >= GOAL:
                        farm.end = t + ACT; return
            else:
                if PREW:
                    c = farm.cells[p]
                    if c.w < thr(t):
                        nn = dose(c, t)
                        if nn:
                            water(c, nn); t = yield t + ACT
            t = yield from plant_ok(p, t)
            # albero extra associato a questo indice
            if idx in exidx:
                q = exidx[idx]
                ec = farm.cells[q]
                if t < T1t or ec.alive:
                    if ec.alive and (t >= T1t or farm.ready_at(q, t) <= t):
                        t = yield t + 2 * ACT; st.moves += 2
                        ok = farm.comp_ok(ec.comp) and farm.ready_at(q, t) <= t
                        farm.harvest(q, t); t = yield t + ACT
                        if ok:
                            st.harv += 1; st.extra_harv += 1; cnt += 1
                        if t < T1t:
                            t = yield from plant_ok(q, t)
                        t = yield t + 2 * ACT; st.moves += 2
                    elif not ec.alive and t < T1t:
                        t = yield t + 2 * ACT; st.moves += 2
                        t = yield from plant_ok(q, t)
                        t = yield t + 2 * ACT; st.moves += 2
            idx = (idx + 1) % n

    gens = []
    di = 0
    for li, lp in enumerate(loops):
        for k in range(K):
            gens.append((di.bit_length() * ACT, drone(di, lp, k)))
            di += 1
    return farm, gens


def ev(n=5, seeds=None, **kw):
    out = []
    for s in (seeds or range(n)):
        f = run(make, seed=s, **kw)
        out.append(f.end / TPS)
    return statistics.mean(out), out


def report(name, n=5, hist=False, **kw):
    mn, out = ev(n, **kw)
    f = run(make, seed=0, **kw)
    st = f.st
    extra = " harv %d ex %d zero %d rr %d water %d wait %.1fs(%d) moves %d" % (
        st.harv, st.extra_harv, st.zero, st.rerolls, st.water, st.wait / TPS / 32, st.waits, st.moves)
    print("%-42s %7.2f  %s%s" % (name, mn, " ".join("%.1f" % x for x in out), extra))
    if hist:
        print("   wait per 10s (s/drone):", " ".join("%d:%.1f" % (b * 10, v / TPS / 32) for b, v in sorted(st.wait_hist.items())))
    sys.stdout.flush()
    return mn


if __name__ == "__main__":
    kw = dict(a.split("=") for a in sys.argv[1:])
    hist = kw.pop("hist", None)
    kw = {k: (float(v) if "." in v else int(v)) for k, v in kw.items()}
    report("v3 " + str(kw), hist=bool(hist), **kw)
