"""dsim4: come dsim.py piu' due opzioni per l'avvio a secco (7 nov 2026):
  Q4   : riscaldamento con 4 erbe in quadrato 2x2 (A, C, B, D; B e D sono gia' erba all'inizio e
         diventano cespugli quando il serbatoio supera THR4); il piano deve avere "B" e "D".
  FERT : nelle attese, se c'e' fertilizzante e mancano piu' di FERT_MIN tick, lo usa (l'erba
         matura subito ma diventa weird: il raccolto successivo rende la meta', Growable.GetYield).
Simulatore tick-esatto di lb_hay_dense / lb_hay_dense2 (32 droni, coppie dense).

Trascrizione del flusso del drone con i costi dell'interprete (FINDINGS_cactus_dino_maze.md):
azione 200, get_*/num_items/can_harvest 1, confronto 1 (Size dell'operando sinistro), if 1,
for 1 per iterazione, while 1 solo alla prima valutazione, `x in dict` Size(x)=3, indice 1,
chiamata propria 1, tupla letterale 1, dict letterale 1+len.
Il mondo (erba, acqua, serbatoio, companion per cella) e' quello di haysim.py.
Ogni azione e ogni lettura dello stato condiviso (serbatoio, fieno) e' preceduta da un
`yield t`, cosi' i droni sono eseguiti in ordine di tempo.

Parametri (dizionario P, vedi BASE):
  plan        lista per drone di dict con moves, plants, A, C (dense/plan*.json)
  pre_a       unita' d'acqua su A PRIMA del primo harvest (0 = come lb_hay_dense: acqua dopo)
  pre_c       idem su C prima del primo harvest
  post_c      acqua su C dopo i reroll del primo ciclo (lb_hay_dense: 1)
  post_a      acqua su A al rientro (lb_hay_dense: 1)
  dict_lit    True: dizionari come letterali (~1+len+2*len tick) invece di ok_dict (~16 per voce)
  W0, EARLY, W, THR, WR, K, NEAR  come nello script
  WN1         unita' per use_item nelle attese (lb_hay_dense: 1)
  WN          unita' per use_item a regime (lb_hay_dense: 2)
  WRN         unita' nel primo ciclo a regime (lb_hay_dense: 2)
"""
import math, json, os, heapq, random
from haysim import Cell, Farm, ACT, YIELD, GOAL, S, TPS, GROW

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN_OPT = os.path.join(HERE, "..", "dense", "plan_opt_acts.json")
INF = float("inf")


def load_plan(path=PLAN_OPT):
    """piano in formato azioni (dense/split.py): [["move",dir]|["plant",[x,y]]|["early","A"|"C"]]"""
    plan = json.load(open(path))
    for p in plan:
        p["A"] = tuple(p["A"]); p["C"] = tuple(p["C"])
        if "B" in p:
            p["B"] = tuple(p["B"]); p["D"] = tuple(p["D"])
        acts = []
        for a in p["actions"]:
            if a[0] == "plant":
                acts.append(("plant", tuple(a[1])))
            elif a[0] == "check":
                acts.append(("check", tuple(a[1]), frozenset(tuple(c) for c in a[2])))
            else:
                acts.append((a[0], a[1]))
        p["actions"] = acts
        p["early"] = any(a[0] == "early" for a in p["actions"])
    return plan


def plan_bushes(plan):
    s = set()
    for p in plan:
        for a in p["actions"]:
            if a[0] == "plant":
                s.add(a[1])
        if "B" in p:
            s.add(p["B"]); s.add(p["D"])
    return s


class Done(Exception):
    pass


class StochCell(Cell):
    """decadimento dell'acqua come nel gioco: ogni 0.1 s, con probabilita' 0.1, acqua *= 0.99"""
    __slots__ = ("rng",)

    def update(self, now):
        dt = now - self.t
        if dt > 0:
            n = int(now // 607.5) - int(self.t // 607.5)
            w0 = self.w
            k = 0
            for _ in range(n):
                if self.rng.random() < 0.1:
                    k += 1
            w1 = w0 * 0.99 ** k
            wavg = (w0 + w1) / 2
            self.prog = min(1.0, self.prog + dt * (1 + 4 * wavg) / GROW)
            self.w = w1
            self.t = now

    def ready_at(self, now):
        self.update(now)
        if self.prog >= 1:
            return now
        return now + (1 - self.prog) * GROW / (1 + 4 * self.w)


BASE = dict(
    init_comp=True, stoch=False, checkers=1, ret_water=0,
    pre_a=0, pre_c=0, post_c=1, post_a=1, dict_lit=False, pre_fallback=1,
    W0=0.4, EARLY=13, W=0.7, THR=64, WR=0.73, K=8, NEAR=50_000_000,
    WN1=1, WN=2, WRN=2, first_wait=True, Q4=False, THR4=40, W4=0.05, FERT=False, FERT_MIN=1500, wn1_fallback=0, start_extra=0, R0=None, R1=None,
)


def spawn_ready(b, n=32):
    """tick a cui il drone b ha finito gli spawn (run_range binario)."""
    ready = {}

    def rr(lo, hi, t):
        t += 3                       # while hi - lo > 1 (prima valutazione)
        while hi - lo > 1:
            mid = (lo + hi) // 2
            t += 2                   # mid = (lo + hi) // 2
            rr(mid, hi, t + ACT)
            t += ACT                 # spawn_drone
            t += 2                   # test del while (solo espressione)
            hi = mid
        ready[lo] = t
    rr(0, n, 0)
    return ready[b]


def drone(farm, b, P):
    t = yield
    main = b < P["checkers"]
    plan = P["plan"][b]
    A, C = plan["A"], plan["C"]
    if P["stoch"]:
        ca = farm.grass.setdefault(A, StochCell()); cc = farm.grass.setdefault(C, StochCell())
        ca.rng = random.Random(hash((farm.seed0, A, "w"))); cc.rng = random.Random(hash((farm.seed0, C, "w")))
    else:
        ca = farm.grass.setdefault(A, Cell())
        cc = farm.grass.setdefault(C, Cell())
    if P["init_comp"]:
        ca.comp = farm.roll(A); cc.comp = farm.roll(C)

    # ---- primitive (generatori: cedono il turno prima dell'effetto)
    def water(cell, t, n):
        """use_item(WATER, n): 200 se il serbatoio ha n unita', altrimenti 1."""
        t = yield t
        if n > 0 and farm.tank(t) >= n:
            farm.water_used += n
            cell.update(t)
            cell.w = min(1.0, cell.w + 0.25 * n)
            farm.nwater += 1
            farm.whist[int(t / TPS)] = farm.whist.get(int(t / TPS), 0) + 1
            return t + ACT, True
        farm.waitw += 1
        farm.hist[int(t / TPS)] = farm.hist.get(int(t / TPS), 0) + 5
        return t + 1, False

    def harvest(cell, pos, t, first=False):
        t = yield t
        cell.update(t)
        if cell.prog >= 1:
            if cell.comp is not None and cell.comp[0] == 0 and farm.bush_time.get(cell.comp[1], INF) <= t:
                farm.hay += YIELD // 2 if pos in farm.weird else YIELD
                farm.nvalid += 1
            elif first and cell.comp is not None and cell.comp[0] == 0 and cell.comp[1] in farm.bush:
                farm.notyet += 1
        elif first:
            farm.unripe += 1
        farm.weird.discard(pos)
        cell.prog = 0.0
        cell.t = t
        cell.comp = farm.roll(pos)
        farm.nharv += 1
        return t + ACT

    def move(t):
        t = yield t
        return t + ACT

    def ok(cell, other):
        return cell.comp[0] == 0 and cell.comp[1] != other and cell.comp[1] in farm.bush

    def goal(t):
        t = yield t
        return farm.hay >= GOAL

    def reroll(cell, pos, other, t):
        """harvest(); while get_companion() not in ok: harvest()"""
        t = yield from harvest(cell, pos, t, True)
        t += 5
        while not ok(cell, other):
            t = yield from harvest(cell, pos, t)
            t += 4
        return t

    def wait(cell, t, rules, pos=None):
        """while not can_harvest(): w = get_water(); if w < r0: use_item(WATER, n0) elif w < r1: ...
        rules = [(soglia, unita'), ...]; con una sola regola il codice e' `if get_water() < W: use_item`"""
        t += 2                           # while + can_harvest
        if P["FERT"] and pos is not None and cell.ready_at(t) > t:
            # if not can_harvest(): if num_items(FERT) >= 1: use_item(FERT)  (prima dell'attesa)
            t += 4
            t = yield t
            r = cell.ready_at(t)
            if r - t > P["FERT_MIN"] and farm.fert(t) >= 1:
                farm.fert_used += 1
                cell.update(t); cell.prog = 1.0
                farm.weird.add(pos); farm.nfert += 1
                return t + ACT
        while True:
            r = cell.ready_at(t)
            if r <= t:
                return t
            chosen = None
            if len(rules) == 1:
                t += 3                   # if get_water() < W
                if cell.w < rules[0][0]:
                    chosen = rules[0][1]
            else:
                t += 1                   # w = get_water()
                for thr, n in rules:
                    t += 2               # confronto + if/elif
                    if cell.w < thr:
                        chosen = n
                        break
            if chosen:
                t, done = yield from water(cell, t, chosen)
                t += 1                   # can_harvest
            else:
                # attesa pura: ogni giro costa (controlli) + 1 (can_harvest)
                per = 4 if len(rules) == 1 else 2 + 2 * len(rules)
                r = cell.ready_at(t)
                n = max(1, math.ceil((r - t) / per))
                farm.waited += n * per
                farm.hist[int(t / TPS)] = farm.hist.get(int(t / TPS), 0) + n * per
                t += n * per
                return t

    def pre_water(cell, t, n):
        t += 3                           # if num_items(WATER) >= n
        t = yield t
        if farm.tank(t) >= n:
            t, _ = yield from water(cell, t, n)
        elif P["pre_fallback"]:
            t, _ = yield from water(cell, t, 1)
        return t

    def first_cycle(cell, pos, other, t):
        """harvest(); while True: while comp[0] != BUSH: harvest(); if comp[1] != other: break; harvest()"""
        t = yield from harvest(cell, pos, t)
        t += 1
        while True:
            t += 4
            while cell.comp[0] != 0:
                t = yield from harvest(cell, pos, t)
                t += 3
            t += 5
            if cell.comp[1] != other:
                break
            t = yield from harvest(cell, pos, t)
        return t

    def early(cell, pos, other, t):
        """c = get_companion(); if c[0] == BUSH and c[1] != other: return  (biglietto valido)
        harvest(); reroll economico come in start()"""
        t += 1 + 1 + 1 + 1 + 1               # c = get_companion(); if c[0] == BUSH
        if cell.comp[0] == 0:
            t += 1 + 2 + 1                   # and c[1] != other
            if cell.comp[1] != other:
                farm.kept += 1
                return t
        t = yield from first_cycle(cell, pos, other, t)
        return t

    # ---- spawn + route
    t = spawn_ready(b)
    t += 2                                   # ROUTES[lo]() indice + chiamata
    for a in plan["actions"]:
        if a[0] == "move":
            t += ACT
        elif a[0] == "plant":
            t = yield t
            farm.bush_time[a[1]] = min(farm.bush_time.get(a[1], INF), t)
            t += ACT
        elif a[0] == "check":
            # c = get_companion(); if c[0] == BUSH: if c[1] in {..}: if can_harvest(): harvest()
            pos, cand = a[1], a[2]
            t += 4
            t = yield t
            if farm.bush_time.get(pos, INF) <= t:
                continue                     # cespuglio: il suo companion non e' mai un cespuglio
            g = farm.grass.get(pos)
            if g is None:
                g = farm.grass[pos] = Cell(); g.comp = farm.roll(pos)
            if g.comp[0] != 0:
                continue
            t += 1 + (1 + 3 * len(cand)) + 2 + 1
            if g.comp[1] not in cand:
                continue
            t += 2
            if g.ready_at(t) > t:
                farm.chk_unripe += 1
                continue
            if farm.bush_time.get(g.comp[1], INF) <= t:
                farm.chk_hit += 1
            else:
                farm.chk_bad += 1
            t = yield from harvest(g, pos, t)
        elif a[0] == "early":
            if a[1] == "A":
                t = yield from early(ca, A, C, t)
            else:
                t = yield from early(cc, C, A, t)
    def old_start(t):
        t += 2                               # PARAMS[lo], chiamata start
        t += 2                               # A = (ax, ay); C = (cx, cy)
        t += P["start_extra"]
        if P["pre_a"]:
            t = yield from pre_water(ca, t, P["pre_a"])
        t = yield from first_cycle(ca, A, C, t)
        t = yield from move(t)
        if P["pre_c"]:
            t = yield from pre_water(cc, t, P["pre_c"])
        t = yield from first_cycle(cc, C, A, t)
        if P["post_c"]:
            t, _ = yield from water(cc, t, P["post_c"])
        t = yield from move(t)
        if P["post_a"]:
            t, _ = yield from water(ca, t, P["post_a"])
        if P["dict_lit"]:
            t += 2 * (1 + 23 + 2 * 23)       # due dict letterali con 23 chiavi (BUSH,(x,y))
        else:
            t += 2 * (24 * 16 + 6)           # ok_dict x2
        t += 1                               # chiamata warmup
        return t

    try:
        if not plan["early"]:
            t = yield from old_start(t)
        else:
            # il percorso finisce su A dopo la visita anticipata: dizionari letterali e warmup
            t += 2                           # PARAMS[lo], chiamata
            if P["Q4"]:
                t += 4 * (1 + 21 + 2 * 21)   # quattro dizionari letterali da 21 voci
            else:
                t += 2 * (1 + 23 + 2 * 23) if P["dict_lit"] else 2 * (24 * 16 + 6)
            t += 1
            if P["Q4"]:
                B, D = plan["B"], plan["D"]
                cb = farm.grass.setdefault(B, Cell()); cd = farm.grass.setdefault(D, Cell())
                cb.comp = farm.roll(B); cd.comp = farm.roll(D)
                quad = ((ca, A, frozenset((C, B, D))), (cc, C, frozenset((A, B, D))),
                        (cb, B, frozenset((A, C, D))), (cd, D, frozenset((A, C, B))))
                R4 = [(P["W4"], 1)]
                done4 = False
                t += 1                       # while True
                while not done4:
                    for k, (cell, pos, ex) in enumerate(quad):
                        t = yield from wait(cell, t, R4, pos)
                        t = yield from harvest(cell, pos, t, True)
                        t += 5
                        while not (cell.comp[0] == 0 and cell.comp[1] in farm.bush and cell.comp[1] not in ex):
                            t = yield from harvest(cell, pos, t)
                            t += 4
                        if k == 1:
                            t += 3           # if num_items(WATER) > THR4
                            t = yield t
                            if farm.tank(t) > P["THR4"]:
                                # move su B, plant, move su D, plant, move su A; okA/okC += B, D
                                t = yield from move(t)
                                t = yield t
                                farm.bush_time[B] = t; farm.grass.pop(B, None); t += ACT
                                t = yield from move(t)
                                t = yield t
                                farm.bush_time[D] = t; farm.grass.pop(D, None); t += ACT
                                t = yield from move(t)
                                t += 4 * 6
                                farm.q4end.append(t / TPS)
                                done4 = True
                                break
                        t = yield from move(t)
                P = dict(P, EARLY=1)
            elif P["ret_water"]:
                # primo ciclo al rientro: harvest+reroll, acqua, mossa (come start() della versione dense)
                t = yield from wait(ca, t, [(P["W0"], P["WN1"])], A)
                t = yield from reroll(ca, A, C, t)
                t, _ = yield from water(ca, t, P["ret_water"])
                t = yield from move(t)
                t = yield from wait(cc, t, [(P["W0"], P["WN1"])], C)
                t = yield from reroll(cc, C, A, t)
                t, _ = yield from water(cc, t, P["ret_water"])
                t = yield from move(t)
        # ---- warmup
        R0 = P["R0"] or [(P["W0"], P["WN1"])]
        R1 = P["R1"] or [(P["W"], P["WN1"])]
        t += 1                               # range()
        for _ in range(P["EARLY"] - 1):
            t += 1                           # for
            t = yield from wait(ca, t, R0, A)
            t = yield from reroll(ca, A, C, t)
            t = yield from move(t)
            t = yield from wait(cc, t, R0, C)
            t = yield from reroll(cc, C, A, t)
            t = yield from move(t)
        t += 3                               # while num_items(WATER) <= THR (prima)
        while True:
            t = yield t
            if farm.tank(t) > P["THR"]:
                break
            t = yield from wait(ca, t, R1, A)
            t = yield from reroll(ca, A, C, t)
            t = yield from move(t)
            t = yield from wait(cc, t, R1, C)
            t = yield from reroll(cc, C, A, t)
            t = yield from move(t)
            t += 2
        farm.p2.append(t / TPS)
        # primo ciclo a regime
        for cell, pos, oth in ((ca, A, C), (cc, C, A)):
            t += 3
            if cell.w < P["WR"]:
                t, _ = yield from water(cell, t, P["WRN"])
            if P["first_wait"]:
                t += 2
                r = cell.ready_at(t)
                if r > t:
                    n = math.ceil(r - t)
                    farm.waited += n; t += n
            t = yield from reroll(cell, pos, oth, t)
            t = yield from move(t)
        t += 1                               # chiamata farm

        # ---- farm / farm_main
        t += 1                               # while True / while num_items(HAY) < NEAR
        while True:
            if main:
                t += 2                       # num_items + confronto
                t = yield t
                if farm.hay >= GOAL - P["NEAR"]:
                    break
            for cyc in range(P["K"]):
                for cell, pos, oth in ((ca, A, C), (cc, C, A)):
                    if cyc == 0:
                        t += 3
                        if cell.w < P["WR"]:
                            t, _ = yield from water(cell, t, P["WN"])
                    t = yield from reroll(cell, pos, oth, t)
                    t = yield from move(t)
        # finale (solo principale): controllo dopo ogni azione
        t += 1
        while True:
            for cell, pos, oth in ((ca, A, C), (cc, C, A)):
                t = yield from harvest(cell, pos, t, True)
                t += 3
                if (yield from goal(t)):
                    farm.end = t + ACT; raise Done
                t += 5
                while not ok(cell, oth):
                    t = yield from harvest(cell, pos, t)
                    t += 3
                    if (yield from goal(t)):
                        farm.end = t + ACT; raise Done
                    t += 4
                t = yield from move(t)
                t += 3
                if (yield from goal(t)):
                    farm.end = t + ACT; raise Done
    except Done:
        return


def run_once(P, seed):
    """Esegue una run; i droni che non sono il principale girano finche' farm.end."""
    B = plan_bushes(P["plan"])
    farm = Farm(random.Random(seed)); farm.seed0 = seed; farm.water_used = 0; farm.fert_used = 0
    farm.end = None; farm.unripe = 0; farm.bush = B; farm.p2 = []
    farm.nwater = 0; farm.nharv = 0; farm.nvalid = 0; farm.waited = 0; farm.waitw = 0
    farm.chk_hit = 0; farm.chk_bad = 0; farm.chk_unripe = 0
    farm.weird = set(); farm.nfert = 0; farm.q4end = []
    farm.bush_time = {}; farm.notyet = 0; farm.kept = 0; farm.hist = {}; farm.whist = {}
    gens = [drone(farm, b, P) for b in range(32)]
    for g in gens:
        next(g)
    heap = [(0, i) for i in range(32)]
    heapq.heapify(heap)
    while heap:
        t, i = heapq.heappop(heap)
        if farm.end is not None and t >= farm.end:
            continue
        try:
            nt = gens[i].send(t)
        except StopIteration:
            continue
        heapq.heappush(heap, (nt, i))
    return farm.end / TPS, farm


if __name__ == "__main__":
    import sys, statistics
    P = dict(BASE, plan=load_plan())
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    ts = []
    for s in range(n):
        T, f = run_once(P, s)
        ts.append(T)
        print("seed %d: %.3f s  harvest %d validi %d acqua(azioni) %d unita' %d attese %d tick (%.3f s/drone) fallite %d unripe %d notyet %d kept %d p2 %.1f-%.1f" % (
            s, T, f.nharv, f.nvalid, f.nwater, f.water_used, f.waited, f.waited / 32 / TPS, f.waitw, f.unripe, f.notyet, f.kept, min(f.p2), max(f.p2)))
    print("media %.3f" % statistics.mean(ts))
