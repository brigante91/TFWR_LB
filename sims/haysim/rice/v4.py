# v4 = v3 + SPLIT: nei primi strati A1 e la A2 dello strato dopo sono intrecciate (raccolta in testa, scavo L righe dietro).
# Sim fedele a lb_rice_multi.py v11 (ultimo strato con kneed, avvio ad albero), con varianti.
# Uso: python v3.py "[{cfg},...]" NSEEDS [SEED0]
from world import *
T = OP  # un tick

def spawn_times(S):
    st = {}
    def rng(lo, hi, t):
        while hi - lo > 1:
            mid = (lo + hi) // 2
            t += ACT
            rng(mid, hi, t + T)
            hi = mid
        st[lo] = t
    rng(0, S, 0.0)
    return st

def mk(GOAL=2000000, MARGIN=25600, KADD=3, W_LOW=0.1, W_POOR=0.25, RICH=100, W_RICH=0.5,
       W_LOW_RICH=0.25, W_WAIT=0.25, FINAL_W=None, FINAL_N=None, STARTS=None, SPAWN="tree",
       A2T=10, BT=5, A1T=2, LOG=None, ROW=None, WAITW=True, ROWRICH=None, HARD=True, A2W=True, SKIPTAIL=None, FINN=None, FMARG=0, NOWL=0, NOWT=0.0, RCACHE=None, RA2=None, RB=None, RFORCE=None, SPL=0, CUTS=(16, 32), LAG=7, BAR=None, BARN=2000, SPLW=True, LB=False, JIT=0.0):
    def prog(w, d, D, r):
        S = w.S
        LAYER = S * S * 128
        st = STARTS or spawn_times(S)
        x = d
        dist = min(d, S - d)
        yield st[d] + dist * (ACT + T) + 2 * T + r.uniform(0, JIT)
        y = 0
        stat = w.stat
        def water_to(tgt):
            w.tank_upd()
            if layer <= NOWL or w.t < NOWT:
                return 12 * T
            n = (tgt - w.wat(x, y)) * 4
            m = -(-n // 1)
            m = min(m, w.tank // 1)
            if m >= 1:
                for _ in range(int(m)):
                    w.tank -= 1; w.add_water(x, y)
                return ACT + 12 * T
            return 12 * T
        if ROW is not None:
            L0, L1, Y0, DH = ROW
            LOWS = [L0 + (L1 - L0) * max(0, yy - Y0) / (S - 1 - Y0) for yy in range(S)]
        def wplant():
            wl = w.wat(x, y)
            if ROW is not None and (ROWRICH is None or (w.tank_upd() or w.tank > ROWRICH)):
                if wl < LOWS[y]: return water_to(min(1.0, LOWS[y] + DH)) + 4 * T
                return 3 * T
            if ROW is not None and ROWRICH is not None:
                w.tank_upd()
                if wl < W_LOW: return water_to(W_POOR) + 5 * T
                return 3 * T
            w.tank_upd()
            if RCACHE is not None:
                if wl < W_LOW_RICH:
                    if rc[0]: return water_to(W_RICH) + 2 * T
                    elif wl < W_LOW: return water_to(W_POOR) + 3 * T
                return 3 * T
            if wl < W_LOW_RICH:
                R = RICH
                if RA2 is not None and ph[0] == "A2": R = RA2
                if RB is not None and ph[0] == "B": R = RB
                if RFORCE is not None:
                    if rf[0]: return water_to(W_RICH) + 3 * T
                    if w.tank > R: return water_to(W_RICH) + 5 * T
                    elif wl < W_LOW: return water_to(W_POOR) + 6 * T
                    return 4 * T
                if w.tank > R: return water_to(W_RICH) + 4 * T
                elif wl < W_LOW: return water_to(W_POOR) + 5 * T
            return 3 * T
        def wait():
            t0 = w.t
            e0 = w.ent[x][y]
            info = (layer, ph[0], y, round(w.wat(x, y), 2), round(e0[1] - w.t, 2) if e0 else None, round(e0[2], 2) if e0 else None)
            if WAITW: yield water_to(W_WAIT)
            while not w.grown(x, y):
                if w.ent[x][y] is None: break
                yield 0.003
            stat["wait"] += w.t - t0
            stat.setdefault("W", []).append(info + (round(w.t - t0, 2),))
            stat.setdefault(("L", layer, ph[0]), 0.0)
            stat[("L", layer, ph[0])] += w.t - t0
        def harvest():
            if w.ent[x][y] is not None:
                w.rice += 128; w.ent[x][y] = None; return ACT
            return T
        def plant(tgt=None, chk=True):
            if w.plant(x, y, r):
                dt = ACT
                if not chk:
                    return dt
                if tgt is not None:
                    dt += water_to(tgt)
                elif ROW is not None or w.wat(x, y) < W_LOW_RICH:
                    dt += wplant()
                return dt + 3 * T
            return T + 3 * T
        def mv():
            nonlocal y
            y = (y + 1) % S
            return ACT
        layer = 0
        rc = [False]
        rf = [False]
        def setrc():
            w.tank_upd(); rc[0] = w.tank > RCACHE
        ph = ["A2"]
        pre = [False]
        while True:
            layer += 1
            # A2
            ph[0] = "A2"
            fin = False
            if FINN is not None and GOAL - w.rice <= 2 * LAYER + FMARG:
                # ultimo strato a n celle: scendi su n, B su n (raccogli+ripianta), A1 su n
                R = GOAL - w.rice
                n = int(-(-R // (S * 256))) + FINN
                n = max(1, min(S, n))
                ph[0] = "FA2"
                for k in range(n):
                    while w.top(x, y) != "clay":
                        yield w.dig(x, y) + 2 * T
                    yield plant() + 2 * T
                    yield mv()
                for k in range(S - n): yield mv()
                ph[0] = "FB"
                for k in range(n):
                    if w.ent[x][y] is not None:
                        if not w.grown(x, y): yield from wait()
                        yield harvest() + 4 * T
                        if w.rice >= GOAL: return
                        yield w.dig(x, y)
                        yield plant(FINAL_W)
                    yield mv() + 2 * T
                for k in range(S - n): yield mv()
                ph[0] = "F1"
                for k in range(n):
                    if w.ent[x][y] is not None:
                        if not w.grown(x, y): yield from wait()
                        yield harvest() + 4 * T
                        if w.rice >= GOAL: return
                    yield mv() + 2 * T
                for k in range(S - n): yield mv()
                stat["fin_idle"] += 1
                continue
            if RCACHE is not None: setrc()
            if RFORCE is not None:
                w.tank_upd(); rf[0] = w.tank > RFORCE
            for k in range(0 if not pre[0] else S, S):
                dt = 0
                while w.top(x, y) != "clay":
                    dt += w.dig(x, y) + (5 if HARD else 2) * T
                    w.ndig += 1
                    yield dt; dt = 0
                yield plant(None, A2W) + 2 * T
                yield mv()
            pre[0] = False
            rem = GOAL - w.rice - LAYER
            ph[0] = "B"
            if rem > LAYER + MARGIN:
                if RCACHE is not None: setrc()
                KT = S
                if SKIPTAIL and layer <= SKIPTAIL[0]: KT = SKIPTAIL[1]
                for k in range(S):
                    if k >= KT:
                        if w.ent[x][y] is not None:
                            if not w.grown(x, y): yield from wait()
                            yield harvest() + 3 * T
                    elif w.grown(x, y):
                        yield harvest()
                        yield w.dig(x, y)
                        yield plant() + BT * T
                    elif w.ent[x][y] is not None:
                        yield from wait()
                        yield harvest()
                        if w.rice >= GOAL: return
                        yield w.dig(x, y)
                        yield plant() + BT * T
                    yield mv()
                ph[0] = "A1"
                if layer <= SPL and rem - LAYER > LAYER + MARGIN:
                    base = (2 * layer - 1) * LAYER
                    hc = 0; dc = 0
                    cuts = CUTS[layer - 1] if isinstance(CUTS[0], tuple) else CUTS
                    lag = LAG[layer - 1] if isinstance(LAG, tuple) else LAG
                    for h in cuts:
                        # raccolta righe [hc, h)
                        while y != hc % S: yield mv()
                        for k in range(hc, h):
                            if w.grown(x, y):
                                yield harvest() + A1T * T
                            elif w.ent[x][y] is not None:
                                yield from wait()
                                yield harvest()
                            yield mv()
                        hc = h
                        dn = S if h >= S else h - lag
                        if dn <= dc: continue
                        if LB:
                            # barriera locale: i vicini Est/Ovest devono aver raccolto la riga h-1
                            t0 = w.t; yy = (h - 1) % S
                            y = yy; yield ACT   # torna sulla riga h-1 (1 mossa a Sud)
                            for _ in range(BARN):
                                if w.ent[(x + 1) % S][yy] is None and w.ent[(x - 1) % S][yy] is None: break
                                yield 6 * T
                            stat["bar"] = stat.get("bar", 0.0) + w.t - t0
                        # torna alla riga dc (direzione piu' corta)
                        nN = (dc - y) % S; nS = (y - dc) % S
                        if nS < nN:
                            for _ in range(nS):
                                y = (y - 1) % S; yield ACT
                        else:
                            for _ in range(nN): yield mv()
                        if BAR is not None:
                            thr = base + min(h, S) * S * 128 - BAR * 128
                            t0 = w.t
                            for _ in range(BARN):
                                if w.rice >= thr: break
                                yield 4 * T
                            stat["bar"] = stat.get("bar", 0.0) + w.t - t0
                        yield 3 * T
                        ph[0] = "D"
                        for k in range(dc, dn):
                            dt = 0
                            while w.top(x, y) != "clay":
                                dt += w.dig(x, y) + 2 * T
                                w.ndig += 1
                                yield dt; dt = 0
                            yield plant(None, SPLW) + 2 * T
                            yield mv()
                        ph[0] = "A1"
                        dc = dn
                    pre[0] = True
                    if LOG is not None and d == 0: LOG.append((layer, round(w.t, 2), w.rice))
                    continue
                for k in range(S):
                    if w.grown(x, y):
                        yield harvest() + A1T * T
                    elif w.ent[x][y] is not None:
                        yield from wait()
                        yield harvest()
                    yield mv()
                    if w.rice >= GOAL: return
                if LOG is not None and d == 0: LOG.append((layer, round(w.t, 2), w.rice))
            else:
                ph[0] = "FB"
                kneed = S
                if rem < LAYER:
                    kneed = max(0, min(S, rem // (S * 128) + KADD))
                for k in range(S):
                    if w.grown(x, y) or w.ent[x][y] is not None:
                        if not w.grown(x, y):
                            yield from wait()
                        yield harvest() + 4 * T
                        if w.rice >= GOAL: return
                        if k < kneed:
                            yield w.dig(x, y)
                            yield plant(FINAL_W)
                    yield mv() + 2 * T
                ph[0] = "F1"
                for k in range(S):
                    if w.ent[x][y] is not None:
                        if not w.grown(x, y):
                            yield from wait()
                        yield harvest() + 4 * T
                        if w.rice >= GOAL: return
                    yield mv() + 2 * T
                stat["fin_idle"] += 1
    return prog

LASTW = []
def runcfg(cfg, seeds):
    ts = []
    for s in seeds:
        World.goal = cfg.get("GOAL", 2000000)
        World.stat = None
        prog = mk(**cfg)
        w0 = {}
        import world
        orig = world.World.__init__
        def init(self, S, seed, _o=orig):
            _o(self, S, seed); self.stat = {"wait": 0.0, "fin_idle": 0}
        world.World.__init__ = init
        try:
            t, w = run(32, 32, prog, s, cfg.get("GOAL", 2000000))
        finally:
            world.World.__init__ = orig
        ts.append((t, w.lost, w.stat["wait"] / 32, w.stat["fin_idle"]))
        LASTW.append(w)
        if cfg.get("LOG") is not None:
            for k in sorted(kk for kk in w.stat if isinstance(kk, tuple)):
                print("   ", k, "%.2f" % (w.stat[k] / 32))
    return ts

if __name__ == "__main__":
    import sys
    cfgs = eval(sys.argv[1]) if len(sys.argv) > 1 else [{}]
    NS = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    S0 = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    for cfg in cfgs:
        res = runcfg(cfg, range(S0, S0 + NS))
        ts = [a[0] for a in res]
        print(cfg, [round(t, 2) for t in ts], "media %.3f" % (sum(ts) / len(ts)),
              "persi", sum(a[1] for a in res) // len(res), "attesa/drone %.1f" % (sum(a[2] for a in res) / len(res)),
              "vuoto", sum(a[3] for a in res) / len(res), "persi max", max(a[1] for a in res), flush=True)
