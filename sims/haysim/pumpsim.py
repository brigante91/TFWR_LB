"""Simulatore della classifica Pumpkins (campo 32x32, 32 droni, 2e8 zucche).

Regole (Pumpkin.cs, Growable.cs, GridManager.cs, Execution.cs):
- crescita 2 s * rf / (1 + 4*acqua), rf uniforme in [1-DEV, 1+DEV]; a fine crescita con prob. 0.2
  la zucca diventa dead_pumpkin (harvest 200, poi ripiantare).
- acqua: serbatoio +1 ogni 20/512 s; use_item(Water, n) = +0.25*n in una sola azione (200 tick),
  fallisce (1 tick, niente consumato) se il serbatoio ha meno di n; la cella decade con prob. 0.1
  ogni 0.1 s di un fattore 0.99 (qui: decadimento continuo medio).
- fertilizzante: +1 ogni 1.25 s; use_item(Fertilizer, n) = grownPercent += 2n s / growTime
  (growTime gia' ridotto dall'acqua: con acqua >= 0.25 e' crescita istantanea); la zucca diventa
  weird (-1536 zucche sulla resa del 32x32). Su dead_pumpkin / cella vuota fallisce (1 tick).
- raccolto del 32x32 completo: 3145728 - 1536*weird. Barriera del main: measure()==measure(West)
  dalla colonna 0 <=> campo completo (i gruppi sono quadrati non avvolti).
- costi: azioni 200 tick (fallite 1), sensori 1, codice ~1 per operazione, 6075 tick = 1 s;
  l'effetto dell'azione e' immediato, poi il drone e' occupato per 200 tick.

I programmi dei droni sono generatori Python che restituiscono (yield) i tick da attendere;
le attese passive (polling di una cella / del campo completo) sono event-driven: il drone viene
risvegliato alla prima iterazione di polling successiva al cambiamento.
"""
import heapq, math, random

TPS = 6075.0
ACT = 200
GROW = 2.0 * TPS            # tick di crescita a secco con rf = 1
DEATH = 0.2
WATER_DT = TPS * 20 / 512   # 237.3 tick per unita' d'acqua
FERT_DT = TPS * 1.25
S = 32
FULL_YIELD = 3145728
WEIRD_PENALTY = 1536
GOAL = 200_000_000
KDECAY = 0.1 * math.log(0.99) / (0.1 * TPS)   # per tick (decadimento medio continuo)

NONE, GROWING, RIPE, DEAD = 0, 1, 2, 3
N, E, So, W = 0, 1, 2, 3
DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]


class Cell:
    __slots__ = ("x", "y", "ent", "w", "tw", "prog", "tp", "rf", "ver", "weird", "gen", "rng",
                 "watchers", "soil", "mnum", "grp")

    def __init__(self, x, y, rng):
        self.x, self.y = x, y
        self.ent = NONE
        self.w = 0.0        # acqua al tempo tw
        self.tw = 0.0
        self.prog = 0.0     # progresso di crescita al tempo tp
        self.tp = 0.0
        self.rf = 1.0
        self.ver = 0
        self.weird = False
        self.gen = 0        # ripiantate consecutive su questa cella nel ciclo corrente
        self.rng = rng
        self.watchers = []
        self.soil = False
        self.mnum = 0       # mysteriousNumber (unico per piantagione)
        self.grp = None     # (x0, y0, lato) del quadrato di appartenenza (solo mature)

    def water(self, t):
        if t > self.tw:
            self.w *= math.exp(KDECAY * (t - self.tw))
            self.tw = t
        return self.w

    def rate(self, t):
        return (1.0 + 4.0 * self.water(t)) / (GROW * self.rf)

    def update(self, t):
        if self.ent == GROWING and t > self.tp:
            self.prog += (t - self.tp) * self.rate(self.tp)
        self.tp = t

    def ready_at(self, t):
        self.update(t)
        if self.prog >= 1.0:
            return t
        return t + (1.0 - self.prog) / self.rate(t)


class World:
    def __init__(self, seed, dev=0.2, goal=GOAL):
        self.seed = seed
        self.dev = dev
        self.goal = goal
        self.t = 0.0
        self.heap = []
        self.seq = 0
        self.cells = [[Cell(x, y, random.Random((seed * 7919 + x) * 104729 + y)) for y in range(S)]
                      for x in range(S)]
        self.ripe = 0
        self.water_used = 0
        self.fert_used = 0
        self.pumpkins = 0
        self.harvests = []       # (t, resa)
        self.complete_watchers = []
        self.drones = []
        self.log = []
        self.done = False
        self.ndead = 0
        self.gen_hist = {}
        # regioni raccoglibili: liste di celle; default il campo intero
        self.regions = [[c for col in self.cells for c in col]]
        self.region_of = {}
        for r in self.regions:
            for c in r:
                self.region_of[(c.x, c.y)] = r
        self.groups_mode = False   # True: fusione reale dei quadrati (PumpkinController)
        self.next_mnum = 1
        self.ripe_mask = None
        self.fallbacks = 0
        self.small_harvests = 0

    def set_regions(self, regions):
        """regions: liste di (x, y). Le celle fuori da ogni regione non sono raccoglibili."""
        self.regions = []
        self.region_of = {}
        for r in regions:
            cells = [self.cells[x][y] for x, y in r]
            self.regions.append(cells)
            for c in cells:
                self.region_of[(c.x, c.y)] = cells

    # --- serbatoi ---
    def tank(self):
        return int(self.t / WATER_DT) - self.water_used

    def fert(self):
        return int(self.t / FERT_DT) - self.fert_used

    # --- eventi ---
    def push(self, t, kind, payload):
        self.seq += 1
        heapq.heappush(self.heap, (t, self.seq, kind, payload))

    def schedule_grow(self, c):
        c.ver += 1
        self.push(c.ready_at(self.t), 1, (c, c.ver))

    def wake(self, watchers):
        for d, poll, t0, wid in watchers:
            if d.wait_id != wid:
                continue
            d.wait_id += 1
            # prossima iterazione di polling dopo l'evento
            n = math.ceil((self.t - t0) / poll)
            if n < 1:
                n = 1
            self.push(t0 + n * poll, 0, d)
        watchers.clear()

    def wake_at(self, d, t, wid):
        self.push(t, 2, (d, wid))

    def set_ent(self, c, ent):
        if c.ent == RIPE:
            self.ripe -= 1
            if self.groups_mode:
                self.ripe_mask[c.x, c.y] = 0
                c.grp = None
        c.ent = ent
        if ent == RIPE:
            self.ripe += 1
        if c.watchers:
            self.wake(c.watchers)
        if self.ripe == S * S and self.complete_watchers:
            self.wake(self.complete_watchers)

    def grow_done(self, c):
        # fine crescita: 20% morte
        c.prog = 1.0
        self.ndead += 0
        if c.rng.random() <= DEATH:
            self.set_ent(c, DEAD)
            self.ndead += 1
        else:
            self.set_ent(c, RIPE)
            if self.groups_mode:
                self.merge(c)

    # --- gruppi (PumpkinController.MergeWithOthers / LargestSquare / HasOverlaps) ---
    def merge(self, c):
        import numpy as np
        m = self.ripe_mask
        m[c.x, c.y] = 1
        # somme prefisse per contare le mature in un rettangolo
        P = np.zeros((S + 1, S + 1), dtype=np.int32)
        P[1:, 1:] = m.cumsum(0).cumsum(1)

        def full(x0, y0, s_):
            return P[x0 + s_, y0 + s_] - P[x0, y0 + s_] - P[x0 + s_, y0] + P[x0, y0] == s_ * s_

        def exists(s_):
            for y0 in range(max(0, c.y - s_ + 1), min(c.y, S - s_) + 1):
                for x0 in range(max(0, c.x - s_ + 1), min(c.x, S - s_) + 1):
                    if full(x0, y0, s_):
                        return True
            return False
        # massimo lato di un quadrato tutto maturo che contiene c (monotono: ricerca binaria)
        lo, hi = 1, S
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if exists(mid):
                lo = mid
            else:
                hi = mid - 1
        smax = lo
        rect = None
        s_ = smax
        while s_ > 1 and rect is None:
            for y0 in range(max(0, c.y - s_ + 1), min(c.y, S - s_) + 1):
                for x0 in range(max(0, c.x - s_ + 1), min(c.x, S - s_) + 1):
                    if not full(x0, y0, s_):
                        continue
                    if not self.has_overlaps(x0, y0, s_):
                        rect = (x0, y0, s_)
                        break
                if rect is not None:
                    break
            s_ -= 1
        if rect is None:
            rect = (c.x, c.y, 1)
        x0, y0, s_ = rect
        base = self.cells[x0][y0].mnum
        for x in range(x0, x0 + s_):
            for y in range(y0, y0 + s_):
                cc = self.cells[x][y]
                cc.grp = rect
                cc.mnum = base
                if cc.watchers:
                    self.wake(cc.watchers)

    def has_overlaps(self, x0, y0, s_):
        for x in range(x0, x0 + s_):
            for y in range(y0, y0 + s_):
                g = self.cells[x][y].grp
                if g is not None:
                    gx, gy, gs = g
                    if gx + gs - 1 > x0 + s_ - 1 or gy + gs - 1 > y0 + s_ - 1 or gx < x0 or gy < y0:
                        return True
        return False

    def enable_groups(self):
        import numpy as np
        self.groups_mode = True
        self.ripe_mask = np.zeros((S, S), dtype=np.int32)

    def plant(self, c):
        c.update(self.t)
        c.ent = GROWING
        c.prog = 0.0
        c.tp = self.t
        c.rf = 1.0 + (2 * c.rng.random() - 1) * self.dev
        c.weird = False
        c.mnum = self.next_mnum
        self.next_mnum += 1
        c.grp = None
        self.schedule_grow(c)

    # --- ciclo principale ---
    def run(self, main_prog, tmax=2000 * TPS, verbose=False):
        self.add_drone(main_prog, 0, 0, 0.0)
        while self.heap and not self.done and self.t < tmax:
            t, _, kind, payload = heapq.heappop(self.heap)
            self.t = t
            if kind == 0:
                d = payload
                try:
                    dt = d.gen.send(None) if d.started else next(d.gen)
                    d.started = True
                except StopIteration:
                    continue
                if dt is None:
                    continue      # il drone si e' messo in attesa su un watcher
                self.push(t + max(dt, 1), 0, d)
            elif kind == 2:
                d, wid = payload
                if d.wait_id == wid:
                    d.wait_id += 1
                    self.push(t, 0, d)
            else:
                c, ver = payload
                if c.ver == ver and c.ent == GROWING:
                    c.update(self.t)
                    if c.prog >= 1.0 - 1e-9:
                        self.grow_done(c)
                    else:
                        self.schedule_grow(c)
        return self

    def add_drone(self, prog, x, y, t):
        d = Drone(self, len(self.drones), x, y)
        d.gen = prog(d)
        self.drones.append(d)
        self.push(t, 0, d)
        return d


class Drone:
    def __init__(self, world, did, x, y):
        self.w = world
        self.id = did
        self.x, self.y = x, y
        self.gen = None
        self.started = False
        self.wait_id = 0

    # --- sensori (1 tick) ---
    def cell(self):
        return self.w.cells[self.x][self.y]

    def get_entity_type(self):
        return self.cell().ent

    def can_harvest(self):
        return self.cell().ent == RIPE

    def get_water(self):
        return self.cell().water(self.w.t)

    def num_water(self):
        return self.w.tank()

    def num_fert(self):
        return self.w.fert()

    def complete(self):
        return self.w.ripe == S * S

    def region_complete(self):
        for cc in self.w.region_of[(self.x, self.y)]:
            if cc.ent != RIPE:
                return False
        return True

    def wait_region(self, poll):
        """Polling (poll tick a iterazione) finche' la regione della cella corrente e' tutta matura."""
        w = self.w
        reg = w.region_of[(self.x, self.y)]
        while True:
            pend = [cc for cc in reg if cc.ent != RIPE]
            if not pend:
                yield poll
                return
            # aspetta un cambiamento della prima cella non matura
            pend[0].watchers.append((self, poll, w.t, self.wait_id))
            yield None

    # --- azioni (200 tick se riuscite) ---
    def move(self, d):
        dx, dy = DIRS[d]
        self.x = (self.x + dx) % S
        self.y = (self.y + dy) % S
        return ACT

    def till(self):
        self.cell().soil = True
        return ACT

    def plant(self):
        c = self.cell()
        if c.ent != NONE:
            return 1
        self.w.plant(c)
        return ACT

    def harvest(self):
        c = self.cell()
        w = self.w
        if c.ent == NONE:
            return 1
        if c.ent == DEAD:
            w.set_ent(c, NONE)
            return ACT
        if c.ent == GROWING:
            c.ver += 1
            w.set_ent(c, NONE)
            return ACT
        if w.groups_mode:
            x0, y0, sz = c.grp
            nweird = 0
            for x in range(x0, x0 + sz):
                for y in range(y0, y0 + sz):
                    cc = w.cells[x][y]
                    if cc.weird:
                        nweird += 1
                    cc.weird = False
                    cc.gen = 0
                    cc.ver += 1
                    w.set_ent(cc, NONE)
            k = min(sz, 6) * 512
            y_ = sz * sz * k - int(nweird * 0.5 * k)
            if sz < 6:
                w.small_harvests += 1
            w.pumpkins += y_
            w.harvests.append((w.t, y_))
            if w.pumpkins >= w.goal:
                w.done = True
            return ACT
        # RIPE: raccoglie il gruppo. Supportato solo il quadrato completo della regione.
        reg = w.region_of[(c.x, c.y)]
        for cc in reg:
            if cc.ent != RIPE:
                raise RuntimeError("raccolto su regione incompleta a t=%.2f" % (w.t / TPS))
        nweird = 0
        for cc in reg:
            if cc.weird:
                nweird += 1
            cc.weird = False
            cc.gen = 0
            cc.ver += 1
            w.set_ent(cc, NONE)
        y = 3072 * len(reg) - WEIRD_PENALTY * nweird
        w.pumpkins += y
        w.harvests.append((w.t, y))
        if w.pumpkins >= w.goal:
            w.done = True
        return ACT

    def water(self, n):
        w = self.w
        if n < 1 or w.tank() < n:
            return 1
        w.water_used += n
        c = self.cell()
        c.update(w.t)
        c.water(w.t)
        c.w = min(1.0, c.w + 0.25 * n)
        if c.ent == GROWING:
            w.schedule_grow(c)
        return ACT

    def fertilize(self, n=1):
        w = self.w
        c = self.cell()
        if c.ent != GROWING and c.ent != RIPE:
            return 1
        if n < 1 or w.fert() < n:
            return 1
        w.fert_used += n
        c.weird = True
        if c.ent == GROWING:
            c.update(w.t)
            c.prog = min(1.0, c.prog + 2.0 * TPS * n * c.rate(w.t))
            if c.prog >= 1.0:
                c.ver += 1
                w.grow_done(c)
            else:
                w.schedule_grow(c)
        return ACT

    def spawn(self, prog):
        w = self.w
        if len(w.drones) >= 32:
            return 1
        w.add_drone(prog, self.x, self.y, w.t + ACT)
        return ACT

    def measure(self, d=None):
        c = self.cell()
        if d is not None:
            dx, dy = DIRS[d]
            c = self.w.cells[(self.x + dx) % S][(self.y + dy) % S]
        if c.ent == GROWING or c.ent == RIPE:
            return c.mnum
        return None

    # --- attese event-driven ---
    def wait_cell(self, poll, seen=None):
        """Equivale a un ciclo di polling (costo `poll` tick a iterazione) finche' l'entita'
        della cella corrente cambia (rispetto a `seen`, se dato). `yield from d.wait_cell(poll)`."""
        if seen is not None and self.cell().ent != seen:
            yield poll
            return
        self.cell().watchers.append((self, poll, self.w.t, self.wait_id))
        yield None

    def wait_measure(self, m0, poll, tmax):
        """while measure() != m0 (e tempo < tmax): pass. Ritorna True se measure() == m0."""
        w = self.w
        t_end = w.t + tmax
        while True:
            if self.measure() == m0:
                return True
            if w.t >= t_end:
                return False
            self.cell().watchers.append((self, poll, w.t, self.wait_id))
            w.wake_at(self, t_end, self.wait_id)
            yield None

    def wait_complete(self, poll):
        if self.w.ripe == S * S:
            yield poll
            return
        self.w.complete_watchers.append((self, poll, self.w.t, self.wait_id))
        yield None


def summarize(w, label=""):
    hs = [t / TPS for t, _ in w.harvests]
    cyc = [b - a for a, b in zip(hs, hs[1:])]
    tot = hs[-1] if hs else float('nan')
    out = {"total": tot, "n": len(hs), "cycles": cyc,
           "mean_cycle": sum(cyc) / len(cyc) if cyc else float('nan'),
           "first": hs[0] if hs else float('nan'), "pumpkins": w.pumpkins}
    if label:
        m, s = divmod(tot, 60)
        print("%-28s totale %6.1f s (%d:%05.2f)  cicli %d  primo %.1f  medio %.2f  min %.2f max %.2f  acqua usata %d fert %d" % (
            label, tot, m, s, out["n"], out["first"], out["mean_cycle"], min(cyc), max(cyc),
            w.water_used, w.fert_used))
    return out
