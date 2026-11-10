# Single, schema "solo r=1": scoperta di r su tutto il campo, poi giro chiuso che passa una volta
# su ogni cella r=1 piantata (fiori T1/T1+D) e usa le celle vuote come corridoio.
import random, sys, statistics
from collections import deque
from opensimplex import OpenSimplex
from sim import Sim, ACT, OP

S = 8
def snake():
    p = []
    for y in range(S):
        xs = range(S) if y % 2 == 0 else range(S - 1, -1, -1)
        p += [y * S + x for x in xs]
    return p

def nbrs(i):
    x, y = i % S, i // S
    return [((x + 1) % S) + y * S, ((x - 1) % S) + y * S, x + ((y + 1) % S) * S, x + ((y - 1) % S) * S]

def build_walk4(planted):
    best = None; tot = 0
    ds = sorted(planted, key=lambda c: sum(1 for nb in nbrs(c) if nb in planted))[:4]
    for st in ds:
        w, ops, dr = build_walk(planted, st)
        tot += ops
        if w is None: continue
        n1 = len(planted) - len(dr)
        if best is None or n1 / len(w) > best[1]:
            best = (w, n1 / len(w), dr)
    return best, tot

def build_walk(planted, start):
    ops = 0
    todo = set(planted); todo.discard(start); walk = [start]; cur = start
    while todo:
        prev = {cur: None}; frontier = [cur]; hits = []
        while frontier and not hits:
            nf = []
            for c in frontier:
                for nb in nbrs(c):
                    ops += 1
                    if nb in prev: continue
                    prev[nb] = c
                    if nb in todo: hits.append(nb)
                    elif nb not in planted: nf.append(nb)
            frontier = nf
        if not hits: break
        hit = min(hits, key=lambda h: sum(1 for nb in nbrs(h) if nb in todo or nb not in planted))
        p = [hit]
        while prev[p[-1]] != cur: p.append(prev[p[-1]])
        walk += p[::-1]; cur = hit; todo.discard(hit)
    dropped = set(todo)
    # ritorno
    prev = {cur: None}; q = deque([cur]); ok = False
    while q and not ok:
        c = q.popleft()
        for nb in nbrs(c):
            ops += 1
            if nb in prev: continue
            prev[nb] = c
            if nb == start: ok = True; break
            if nb not in planted or nb in dropped: q.append(nb)
    if not ok: return None, ops, dropped
    p = [start]
    while prev[p[-1]] != cur: p.append(prev[p[-1]])
    walk += p[::-1][:-1]
    return walk, ops, dropped

def run(T1=6, D=5, K=5, WS=1.0, WT=1.0, WLOW=0.6, MARGIN=0.05, OPS_PER=15, seed=1, goal=2.5e7, tmax=900):
    rng = random.Random(seed)
    ns = OpenSimplex(seed + 1000)
    rmap = [1 if ns.noise2((i % S) / 2 + 97, (i // S) / 2 + 97) > 0 else 0 for i in range(S * S)]
    sim = Sim(S * S, rng, 25.6, rmap)
    M1 = T1 - 1; M2 = T1 + D - 1
    cnt = {}
    def water_to(tgt, low):
        w = sim.get_water()
        if w < low and sim.tank() >= 1:
            sim.water(max(1, int((tgt - w) * 4)))
    def new_plant():
        sim.plant()
        while sim.measure() != M1:
            sim.harvest(); sim.plant()
    # scoperta
    sn = snake(); planted = set()
    for k in range(S * S):
        j = sn[(k + 1) % (S * S)]
        if k + 1 < S * S:
            sim.move_to(j)
            sim.till()
            ok = False
            for t in range(K):
                sim.plant(); m = sim.measure()
                if m == M1: ok = True; break
                sim.harvest()
                if m == 2: break    # f1 = 3: r = 0
            if ok:
                planted.add(j); water_to(WS, WS)
        else:
            sim.move_to(j)          # torna a (0,0), che resta vuota
    cnt["setup"] = sim.nact
    best, ops = build_walk4(planted)
    if best is None:
        return None
    walk, eta, dropped = best
    sim.ops(ops * OPS_PER)
    # ascensore: la prima cella vuota del giro; il giro ruota per partire da li'
    e = next(k for k in range(len(walk)) if walk[k] not in planted or walk[k] in dropped)
    walk = walk[e:] + walk[:e]
    # trasferimento da (0,0) all'ascensore: a quota 18, senza tagliare nulla
    sim.hover(18)
    sim.t += ACT * 4; sim.nact += 4
    sim.pos = walk[0]
    L = len(walk)
    isp = [walk[k] in planted and walk[k] not in dropped for k in range(L)]
    cnt["n1"] = sum(isp); cnt["L"] = L
    bad = [False] * L
    prev_end = sim.t; wmin = 0.0; need1 = M1
    cnt['eta'] = eta
    sweep = (L - 1) * (ACT + 3 * OP)
    def guard(blocks):
        sim.wait_until(prev_end + blocks / (1 + 4 * wmin) + MARGIN - sweep)
    nrr = 0
    while sim.t < tmax:
        guard(need1)
        sim.hover(M1)
        for k in range(1, L):
            sim.move_to(walk[k])
            if isp[k]:
                m = sim.measure()
                if m != M2 and m != M1:
                    bad[k] = True
        sim.move_to(walk[0]); prev_end = sim.t
        guard(D)
        sim.hover(M2)
        emax = 3
        for k in range(1, L):
            sim.move_to(walk[k])
            if isp[k]:
                mm = sim.measure()
                if mm > M2 and mm - M2 > emax: emax = mm - M2
        if emax > 5: emax = 5
        sim.move_to(walk[0]); prev_end = sim.t
        guard(emax)
        sim.hover(1)
        wm = 1.0; rer = False
        for k in range(1, L):
            sim.move_to(walk[k])
            if not isp[k]: continue
            if sim.bamboo >= goal:
                sim.cnt = cnt; cnt["nrr"] = nrr; return sim
            if bad[k]:
                sim.harvest(); new_plant(); bad[k] = False; rer = True; nrr += 1
            water_to(WT, WLOW)
            w = sim.cur().water_at(sim.t)
            if w < wm: wm = w
        need1 = M1 if rer else T1 - 2
        sim.move_to(walk[0]); prev_end = sim.t
        wmin = wm * 0.97
    sim.cnt = cnt; cnt["nrr"] = nrr
    return sim

if __name__ == "__main__":
    kw = {}
    for a in sys.argv[1:]:
        k, v = a.split("="); kw[k] = float(v) if "." in v else int(v)
    N = kw.pop("N", 8)
    res = []; tot = {}; fails = 0
    for s in range(N):
        sim = run(seed=s, **kw)
        if sim is None: fails += 1; continue
        res.append(sim.t)
        for k, v in sim.cnt.items(): tot[k] = tot.get(k, 0) + v
        tot["act"] = tot.get("act", 0) + sim.nact
        tot["wait"] = tot.get("wait", 0) + sim.stats["wait"]
    n = len(res)
    print(kw, "t=%.1f +- %.1f" % (statistics.mean(res), statistics.pstdev(res)), "fail", fails, {k: round(v / n, 1) for k, v in tot.items()})
