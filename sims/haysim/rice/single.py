# trascrizione di lb_rice_single.py nel simulatore, con varianti della discesa (A2)
from world import *
OVV = 12*OP   # interprete per visita
def snake(S):
    cells=[]
    for c in range(S):
        ys = range(S) if c % 2 == 0 else range(S-1, -1, -1)
        cells += [(c, y) for y in ys]
    return cells
import copy
def orient(S, o):
    base = snake(S)
    out = []
    for (x, y) in base:
        if o & 4: x, y = y, x
        if o & 1: x = S - 1 - x
        if o & 2: y = S - 1 - y
        out.append((x, y))
    return out
def mk(PUMP=0, PUMP_OFF=0, START=0, H_SKIP=6, SLOW=0.15, stats=None, ORACLE=False, PLANE=False, PROBE=False):
    def prog(w, d, D, r):
        S = w.S; cells = snake(S); n = len(cells)
        cells = cells[START:] + cells[:START]
        def water_full(x, y):
            if w.water[x][y] < SLOW:
                w.tank_upd()
                k = min(int((1 - w.water[x][y]) * 4), int(w.tank))
                if k >= 1:
                    for _ in range(k): w.tank -= 1; w.add_water(x, y)
                    return ACT
            return 0
        def dig_to_clay(x, y):
            t = 0
            while w.top(x, y) != "clay" and GROUNDS[w.top(x, y)][0] <= H_SKIP:
                t += w.dig(x, y) + 5*OP; w.ndig += 1
            return t
        def harvest_wait(x, y):
            t = 0
            while not w.grown(x, y): t += 0.005; yield 0.005
            w.rice += 128; w.ent[x][y] = None
        while True:
            need = -(-(w.goal - w.rice) // 128)
            if need + 2 < n:
                lim = need + 2
                for (x, y) in cells[:lim]:
                    yield dig_to_clay(x, y)
                    if w.plant(x, y, r): yield ACT
                    w.water[x][y] = max(w.water[x][y], 0); yield water_full(x, y) or 0
                    yield ACT
                for (x, y) in reversed(cells[:lim]):
                    yield ACT
                    if w.ent[x][y] is not None:
                        yield from harvest_wait(x, y); yield ACT
                        if w.rice >= w.goal: return
                continue
            # A2
            if ORACLE:
                best = None
                for o in range(8):
                    cs = orient(S, o)
                    ww = copy.deepcopy(w); tt = 0
                    for (x, y) in cs:
                        while ww.top(x, y) != "clay" and GROUNDS[ww.top(x, y)][0] <= H_SKIP:
                            tt += ww.dig(x, y)
                    if best is None or tt < best[0]: best = (tt, cs)
                old = cells[0]; cells = best[1]
                dx = min((cells[0][0]-old[0]) % S, (old[0]-cells[0][0]) % S); dy = min((cells[0][1]-old[1]) % S, (old[1]-cells[0][1]) % S)
                yield ACT * (dx + dy)
            if PLANE or PROBE:
                def clayz(x, y):
                    z = w.depth[x][y]
                    while w.ground(x, y, z) != "clay": z += 1
                    return z
                if PLANE:
                    gx = sum(clayz(x+1, y) - clayz(x, y) for x in range(S-1) for y in range(S))
                    gy = sum(clayz(x, y+1) - clayz(x, y) for x in range(S) for y in range(S-1))
                else:
                    # sonda: scava la cella d'angolo attuale e guarda se i vicini trascinati sono gia' argilla
                    x0, y0 = cells[0]
                    yield dig_to_clay(x0, y0)
                    sx = 1 if x0 == 0 else -1; sy = 1 if y0 == 0 else -1
                    ex = w.top(x0+sx, y0) == "clay"; ey = w.top(x0, y0+sy) == "clay"
                    # argilla piu' in alto verso +sx -> pendenza negativa lungo x nel verso di marcia
                    gx = (-1 if ex else 0) * sx; gy = (-1 if ey else 0) * sy
                    if not ex and not ey: gx = gy = 0
                # vogliamo procedere verso l'argilla meno profonda: asse maggiore = pendenza piu' forte
                o = 0
                if abs(gy) > abs(gx): o |= 4; gx, gy = gy, gx
                if gx > 0: o |= 1
                if gy > 0: o |= 2
                if PROBE and gx == 0 and gy == 0: o = None
                if o is not None:
                    old = cells[0]; cells = orient(S, o)
                    dx = min((cells[0][0]-old[0]) % S, (old[0]-cells[0][0]) % S); dy = min((cells[0][1]-old[1]) % S, (old[1]-cells[0][1]) % S)
                    yield ACT * (dx + dy)
            for i, (x, y) in enumerate(cells):
                yield dig_to_clay(x, y) + OVV
                if PUMP and i % PUMP == PUMP_OFF and w.top(x, y) == "clay":
                    yield w.dig(x, y); w.ndig += 1   # pompa: mangia il 1o blocco, trascina i vicini all'argilla
                if w.plant(x, y, r):
                    yield ACT + water_full(x, y)
                yield ACT
            # B
            for (x, y) in cells:
                if w.ent[x][y] is not None:
                    yield from harvest_wait(x, y); yield ACT + OVV
                    if w.rice >= w.goal: return
                    yield w.dig(x, y); w.ndig += 1
                if w.top(x, y) == "clay" and w.plant(x, y, r):
                    yield ACT + water_full(x, y)
                yield ACT
            # A1
            for (x, y) in cells:
                if w.ent[x][y] is not None:
                    yield from harvest_wait(x, y); yield ACT + OVV
                    if w.rice >= w.goal: return
                yield ACT
    return prog
if __name__ == "__main__":
    import sys
    cfgs = eval(sys.argv[1]) if len(sys.argv) > 1 else [{}]
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    World.goal = 100000
    for cfg in cfgs:
        ts=[]; dg=[]; lost=[]
        for s in range(N):
            t, w = run(8, 1, mk(**cfg), s, 100000); ts.append(t); dg.append(w.ndig); lost.append(w.lost)
        print(cfg, "t %.2f" % (sum(ts)/N), "scavi %.0f" % (sum(dg)/N), "persi %.1f" % (sum(lost)/N), flush=True)
