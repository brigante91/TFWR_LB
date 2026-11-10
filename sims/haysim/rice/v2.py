from world import *
OV = 6*OP
def wd(S, a, b):
    dx = abs(a[0]-b[0]); dy = abs(a[1]-b[1])
    return min(dx, S-dx) + min(dy, S-dy)
def block_path(S, D, d, bw):
    bh = S * S // D // bw
    nbx = S // bw
    x0 = (d % nbx) * bw; y0 = (d // nbx) * bh
    if bh == S and bw == 1:
        return [(x0, y) for y in range(S)]
    cells = [(x0 + x, y0) for x in range(bw)]          # riga 0 verso Est
    for j in range(1, bh):                              # righe 1..bh-1 a serpentina sulle colonne 1..bw-1
        xs = range(bw - 1, 0, -1) if j % 2 == 1 else range(1, bw)
        cells += [(x0 + x, y0 + j) for x in xs]
    cells += [(x0, y0 + j) for j in range(bh - 1, 0, -1)]   # colonna 0 in giu'
    return cells
def path(S, D, d):
    x0 = d*S//D; x1 = (d+1)*S//D; cells = []
    for c in range(x0, x1):
        ys = range(S) if (c-x0) % 2 == 0 else range(S-1, -1, -1)
        cells += [(c, y) for y in ys]
    return cells
def mk(SYNC=1.5, WTH=0.07, MAXD=24, water=True, PRE=0.0, RICH=0, RTGT=0.5, FIRST=0, FTGT=0.25, A1DIG=True, SKIPB=0.0, FERT=False, PREB=True, BW=0, INF=False, WAIT_TGT=0.25, TAILB=0, TAILB_TGT=0.5, HEADA=0, HEADA_TGT=0.5, BSCARCE=False, ASCARCE=False, SCARCE_TH=None, PREDIG=0, PRELAYERS=2, KMIN=20, PRESAFE=False):
    def prog(w, d, D, r):
        S = w.S
        cells = block_path(S, D, d, BW) if BW else path(S, D, d)
        mc = [wd(S, cells[i], cells[(i+1) % len(cells)]) for i in range(len(cells))]
        yield ACT * 5 + ACT * wd(S, (0, 0), cells[0])
        if INF: w.tank = 1e9
        def wait_grown(x, y):
            if w.ent[x][y][1] > w.t and water and w.wat(x, y) < WAIT_TGT:
                w.tank_upd(); used = False
                while w.wat(x, y) < WAIT_TGT - 1e-9 and w.tank >= 1:
                    w.tank -= 1; w.add_water(x, y); used = True
                if used: yield ACT
            if FERT and w.ent[x][y][1] > w.t and w.fert_get():
                w.ent[x][y][1] = max(w.t, w.ent[x][y][1] - 2.0); w.ent[x][y].append("weird"); yield ACT
            while not w.grown(x, y): yield 0.005
        def pre(x, y, k=99, ph="A"):
            w.tank_upd()
            tgt = PRE
            n = len(cells)
            scarce = w.tank < (SCARCE_TH if SCARCE_TH is not None else RICH)
            if ph == "B" and k >= n - TAILB: tgt = max(tgt, TAILB_TGT)
            if ph == "A" and k < HEADA: tgt = max(tgt, HEADA_TGT)
            if ph == "B" and BSCARCE and scarce and k < n - TAILB: tgt = 0
            if ph == "A" and ASCARCE and scarce and k >= HEADA: tgt = 0
            if RICH and w.tank >= RICH: tgt = max(tgt, RTGT)
            if k < FIRST: tgt = max(tgt, FTGT)
            used = False
            while w.wat(x, y) < tgt and w.tank >= 1:
                w.tank -= 1; w.add_water(x, y); used = True
            if used: yield ACT
        def harvest(x, y):
            w.rice += 64 if "weird" in w.ent[x][y] else 128; w.ent[x][y] = None; yield ACT + OV
        def drop(x, y):
            if SYNC > 0:
                t0 = w.t
                while w.t - t0 < SYNC:
                    bad = False
                    for a in (x-1, x+1):
                        if 0 <= a < S and w.top(a, y) in ("terrace", "dry"): bad = True
                    if not bad: break
                    yield 0.005
            n = 0
            while w.top(x, y) != "clay" and n < MAXD:
                yield w.dig(x, y) + OV; n += 1; w.ndig += 1
            if w.plant(x, y, r):
                yield ACT
                yield from pre(x, y, kk)
        phase = "A2"
        layer = 0; predone = False
        while True:
            if phase == "A2": layer += 1; predone = False
            for kk, (x, y) in enumerate(cells):
                if phase == "A2":
                    if PREDIG and kk < PREDIG and w.ent[x][y] is not None:
                        yield 2*OP + ACT * mc[kk]; continue
                    yield from drop(x, y)
                elif phase == "B":
                    if w.ent[x][y] is not None and w.t < SKIPB and not w.grown(x, y):
                        pass
                    elif w.ent[x][y] is not None:
                        yield from wait_grown(x, y); yield from harvest(x, y)
                        if w.rice >= w.goal: return
                        yield w.dig(x, y) + OV
                    if w.top(x, y) == "clay" and w.plant(x, y, r):
                        yield ACT
                        if PREB: yield from pre(x, y, kk, "B")
                else:
                    if (PREDIG and not predone and layer <= PRELAYERS and kk >= KMIN
                            and w.ent[x][y] is not None and w.ent[x][y][1] > w.t):
                        n = len(cells)
                        x0, y0 = cells[0]
                        if PRESAFE and ((x0 > 0 and w.ent[x0-1][y0] is not None) or (x0 < w.S-1 and w.ent[x0+1][y0] is not None)):
                            if getattr(w, "DRONELOG", False): print("   drone", d, "salta predig strato", layer, "t %.1f" % w.t)
                            yield 4*OP
                        else:
                          predone = True
                          yield ACT * (n - kk)                      # verso la cella 0 (wrap)
                          for j in range(PREDIG):
                              xj, yj = cells[j]
                              yield from drop(xj, yj)
                              yield ACT
                          yield ACT * (n - kk + PREDIG)             # ritorno alla cella kk
                          if w.ent[x][y] is None: yield ACT * mc[kk]; continue
                    if w.ent[x][y] is not None:
                        yield from wait_grown(x, y); yield from harvest(x, y)
                        if w.rice >= w.goal: return
                    if A1DIG and w.top(x, y) == "dry": yield w.dig(x, y) + OV
                yield ACT * mc[kk] + OV
            phase = {"A2": "B", "B": "A1", "A1": "A2"}[phase]
            if phase == "A2" and getattr(w, "DRONELOG", False):
                w.lay.setdefault(d, []).append(round(w.t, 1))
            if phase == "A2" and d == 0 and getattr(w, "LAYERLOG", False):
                w.tank_upd(); print("  strato fine t %.2f riso %d acqua %d" % (w.t, w.rice, w.tank), flush=True)
    return prog
if __name__ == "__main__":
    import sys
    cfgs = eval(sys.argv[1]) if len(sys.argv) > 1 else [{}]
    for cfg in cfgs:
        for mode, S, D in (("multi", 32, 32), ("single", 8, 1)):
            ts = []; lost = 0
            NS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            for s in range(NS):
                World.goal = GOALS[mode]
                t, w = run(S, D, mk(**cfg), s, GOALS[mode]); ts.append(t); lost += w.lost
            print(cfg, mode, [round(t, 1) for t in ts], "media %.2f" % (sum(ts)/len(ts)), "persi", lost//len(ts), "scavi A2", w.ndig, flush=True)
