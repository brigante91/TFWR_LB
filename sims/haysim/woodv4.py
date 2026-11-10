"""lb_wood_v2: giri indipendenti da 8 alberi + "fix" dei companion: se il companion e' (erba|cespuglio, q)
con q sul proprio percorso, invece del reroll il drone cambia il contenuto di q quando ci passa
(plant(Bush) sull'erba o harvest() del cespuglio: 200 tick, zero mosse).  Le celle di percorso di
altri droni (F/X) sono escluse (contenuto imprevedibile).  Le carote costano fieno: mai piantabili."""
import sys, os, math, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from woodsim import Farm, run, ACT, TPS, GOAL, YIELD, WATER_DT, S
from woodlay import ladder_tours, route_cells, dist, wrap, DIAMOND, shape_tours, RING8

NH = GOAL // YIELD + (1 if GOAL % YIELD else 0)


class Stats:
    def __init__(self):
        self.wait = 0; self.water = 0; self.rerolls = 0; self.harv = 0; self.moves = 0
        self.zero = 0; self.waits = 0; self.fix = 0; self.restore = 0; self.acc_fix = 0; self.acc_g = 0
        self.conflict = 0; self.wait_hist = {}


class FarmB(Farm):
    """Farm con celle a cespuglio."""
    def __init__(self, seed, tree_cells):
        Farm.__init__(self, seed, tree_cells)
        self.bush = set()
    def comp_ok(self, comp):
        k, q = comp
        if k == 2: return False
        if q in self.cells and self.cells[q].alive: return False
        if k == 0: return q not in self.bush
        return q in self.bush


def make(seed, tours=None, FIX=1, ROUTES=1, FOREIGN=0, RESTORE=0, W=0.9, WN=0, W0=0.5, T0=30.0,
         RES=0, GATE=40, OV_STEP=6, OV_PLANT=10, OV_RR=1, OV_FIXCHK=3, WAIT_Q=6, PREW=1):
    st = Stats()
    tours = tours or ladder_tours()
    trees = {}
    for ti, tr in enumerate(tours):
        for p in tr: trees[p] = ti
    # percorsi: route di default per passo (0 = x prima); ROUTES=1 -> solo default; 2 -> entrambe disponibili
    paths = []
    for tr in tours:
        steps = []
        for k in range(8):
            a, b = tr[k], tr[(k + 1) % 8]
            r0 = route_cells(a, b, 0); r1 = route_cells(a, b, 1)
            steps.append((r0, r1 if (ROUTES == 2 and r1 != r0) else r0))
        paths.append(steps)
    owner = {}
    for ti, steps in enumerate(paths):
        for (r0, r1) in steps:
            for q in set(r0) | set(r1):
                owner.setdefault(q, set()).add(ti)
    mine = []   # per drone: insieme celle di percorso esclusive
    for ti, steps in enumerate(paths):
        s = set()
        for (r0, r1) in steps:
            for q in set(r0) | set(r1):
                if len(owner[q]) == 1: s.add(q)
        mine.append(s)
    farm = FarmB(seed, list(trees))
    farm.st = st
    per_drone = NH // 32
    T0t = T0 * TPS

    def thr(t):
        return W0 if (W0 is not None and t < T0t) else W

    def dose(c, t):
        tk = farm.tank(t) - RES
        if tk <= 0: return 0
        if WN: return WN if tk >= WN else 0
        need = int(math.ceil((1.0 - c.w) / 0.25 - 1e-9))
        return max(0, min(need, tk))

    def water(c, n):
        farm.water_used += n; c.w = min(1.0, c.w + 0.25 * n); st.water += 1

    def wait_ready(p, t):
        first = True
        while True:
            r = farm.ready_at(p, t)
            if r <= t or farm.end is not None: return t
            c = farm.cells[p]
            if c.w < thr(t):
                n = dose(c, t)
                if n:
                    water(c, n); t = yield t + ACT; continue
                nxt = (math.floor(t / WATER_DT) + 1) * WATER_DT
                r = min(r, nxt)
            if first: st.waits += 1; first = False
            d = max(WAIT_Q, math.ceil((r - t) / WAIT_Q) * WAIT_Q)
            st.wait += d
            b = int(t / TPS) // 10
            st.wait_hist[b] = st.wait_hist.get(b, 0) + d
            t = yield t + d

    def drone(di, tr):
        t = yield
        steps = paths[di]
        myset = mine[di]
        # stato delle celle di percorso (dal punto di vista del drone): contenuto previsto e domanda
        content = {q: 0 for q in myset}     # 0 erba, 1 cespuglio (contenuto atteso dopo i fix pendenti)
        demand = {q: 0 for q in myset}
        todo = {}                           # q -> contenuto da realizzare al passaggio
        route_choice = [0] * 8              # per passo, quale route usare al prossimo passaggio
        pin = [None] * 8                    # per albero: cella di percorso impegnata dal suo companion
        # celle "solo erba" per albero: rombo meno alberi, meno celle di percorso (proprie o altrui)
        gonly = []
        for p in tr:
            s = set()
            for (dx, dy) in DIAMOND:
                q = wrap((p[0] + dx, p[1] + dy))
                if q in trees: continue
                if q in owner and not (FOREIGN and q not in myset): continue
                s.add(q)
            gonly.append(s)
        pos = (0, 0)
        cnt = 0
        k = 0
        first_lap = True
        # avvicinamento
        d0 = dist(pos, tr[0]); t = yield t + d0 * ACT; st.moves += d0; pos = tr[0]
        while True:
            p = tr[k]
            if farm.end is not None: return
            cell = farm.cells[p]
            if cell.alive:
                t = yield from wait_ready(p, t)
                if farm.end is not None: return
                ok = farm.comp_ok(cell.comp)
                farm.harvest(p, t); t = yield t + ACT
                st.harv += 1; cnt += 1
                if not ok: st.zero += 1
                if pin[k] is not None:
                    demand[pin[k]] -= 1; pin[k] = None
                    t += 4
                if cnt >= per_drone - GATE:
                    t += 2
                    if farm.wood >= GOAL:
                        farm.end = t + ACT; return
            elif PREW:
                c = farm.cells[p]
                if c.w < thr(t):
                    nn = dose(c, t)
                    if nn: water(c, nn); t = yield t + ACT
            # pianta con reroll / fix
            while True:
                comp = farm.plant(p, t)
                t = yield t + ACT + OV_PLANT
                ck, q = comp
                if ck == 0 and q in gonly[k]:
                    st.acc_g += 1; break
                if FIX and ck != 2 and q in myset:
                    want = ck   # 0 erba, 1 cespuglio
                    if content[q] == want:
                        demand[q] += 1; pin[k] = q; st.acc_fix += 1; t += 6; break
                    if demand[q] == 0:
                        content[q] = want; todo[q] = want; demand[q] = 1; pin[k] = q
                        st.acc_fix += 1; st.fix += 1; t += 8
                        break
                    st.conflict += 1
                st.rerolls += 1
                farm.harvest(p, t)
                t = yield t + ACT + OV_RR
            # passo verso il prossimo albero, applicando i fix sulle celle attraversate
            r0, r1 = steps[k]
            route = r0
            if ROUTES == 2 and r1 is not r0:
                # scegli la route che contiene un fix pendente (se entrambe: la 0; l'altra aspetta)
                if any(q in todo for q in r1) and not any(q in todo for q in r0):
                    route = r1
            nb = tr[(k + 1) % 8]
            d = dist(p, nb)
            st.moves += d
            if todo:
                t += OV_FIXCHK * len(route)
            # il drone attraversa le celle: fix in sequenza
            tt = t
            for q in route:
                tt += ACT   # mossa
                if q in todo:
                    want = todo.pop(q)
                    if want == 1:
                        farm.bush.add(q)
                    else:
                        farm.bush.discard(q)
                    tt += ACT
                elif RESTORE and q in farm.bush and q in myset and demand[q] == 0 and content[q] == 1:
                    farm.bush.discard(q); content[q] = 0; tt += ACT; st.restore += 1
            tt += ACT   # ultima mossa (arrivo sull'albero)
            t = yield tt + OV_STEP
            pos = nb
            k = (k + 1) % 8
            if k == 0: first_lap = False

    gens = []
    for di, tr in enumerate(tours):
        gens.append((di.bit_length() * ACT, drone(di, tr)))
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
    extra = " harv %d zero %d rr %d accG %d accF %d fix %d rest %d confl %d water %d wait %.1fs moves %d" % (
        st.harv, st.zero, st.rerolls, st.acc_g, st.acc_fix, st.fix, st.restore, st.conflict, st.water,
        st.wait / TPS / 32, st.moves)
    print("%-44s %7.2f  %s%s" % (name, mn, " ".join("%.1f" % x for x in out), extra))
    if hist:
        print("   wait per 10s (s/drone):", " ".join("%d:%.1f" % (b * 10, v / TPS / 32) for b, v in sorted(st.wait_hist.items())))
    sys.stdout.flush()
    return mn


if __name__ == "__main__":
    kw = dict(a.split("=") for a in sys.argv[1:])
    hist = kw.pop("hist", None)
    lay = kw.pop("lay", "ladder")
    kw = {k: (float(v) if "." in v else int(v)) for k, v in kw.items()}
    tours = None
    if lay == "ring8":
        tours = shape_tours(RING8, (8, 0), (2, 4), 4, 8)
    report("v4 %s %s" % (lay, kw), hist=bool(hist), tours=tours, **kw)
