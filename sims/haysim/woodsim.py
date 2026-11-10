"""Leaderboard Wood: 1e10 legno, 32 droni. Regole dall'IL/asset:
albero 7 s x 2^(alberi adiacenti) / (1+4w) x U(0.8,1.2); resa 409600 con companion.
harvest 200 (rimuove l'albero, torna erba), plant 200 (estrae il companion).
Companion: tipo uniforme {grass,bush,carrot}, posizione uniforme nel rombo r=3."""
import heapq, random, math, statistics
TPS = 6075.0; ACT = 200; GOAL = 10_000_000_000; YIELD = 409600
WATER_DT = TPS * 20 / 512
S = 32
DIAMOND = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) if (dx or dy) and abs(dx) + abs(dy) <= 3]
DECAY_K = 0.1 * math.log(0.99) / 607.5


class Tree:
    __slots__ = ("w", "prog", "t", "dur", "comp", "alive")
    def __init__(self):
        self.w = 0.0; self.prog = 0.0; self.t = 0.0; self.dur = 1.0; self.comp = None; self.alive = False


class Farm:
    def __init__(self, seed, tree_cells):
        self.rng = random.Random(seed)
        self.cells = {p: Tree() for p in tree_cells}
        self.wood = 0; self.water_used = 0; self.end = None; self.t_goal = None
    def tank(self, t):
        return int(t / WATER_DT) - self.water_used
    def ntrees(self, p):
        c = 0
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = ((p[0] + d[0]) % S, (p[1] + d[1]) % S)
            if q in self.cells and self.cells[q].alive:
                c += 1
        return c
    def update(self, p, t):
        c = self.cells[p]
        dt = t - c.t
        if dt > 0:
            w1 = c.w * math.exp(DECAY_K * dt)
            if c.alive:
                c.prog = min(1.0, c.prog + dt * (1 + 2 * (c.w + w1)) / c.dur)
            c.w = w1; c.t = t
        return c
    def ready_at(self, p, t):
        c = self.update(p, t)
        if c.prog >= 1: return t
        return t + (1 - c.prog) * c.dur / (1 + 4 * c.w)
    def plant(self, p, t):
        c = self.update(p, t)
        c.alive = True; c.prog = 0.0
        c.dur = 7 * TPS * (2 ** self.ntrees(p)) * self.rng.uniform(0.8, 1.2)
        k = self.rng.randrange(3)
        dx, dy = DIAMOND[self.rng.randrange(24)]
        c.comp = (k, ((p[0] + dx) % S, (p[1] + dy) % S))
        return c.comp
    def comp_ok(self, comp):
        q = comp[1]
        return comp[0] == 0 and not (q in self.cells and self.cells[q].alive)
    def harvest(self, p, t):
        c = self.update(p, t)
        if c.alive and c.prog >= 1 and self.comp_ok(c.comp):
            self.wood += YIELD
            if self.wood >= GOAL and self.t_goal is None:
                self.t_goal = t
        c.alive = False


def run(make, seed=0, **kw):
    farm, gens = make(seed, **kw)
    heap = []
    for i, (t0, g) in enumerate(gens):
        next(g); heap.append((t0, i))
    heapq.heapify(heap)
    gs = [g for _, g in gens]
    while heap:
        t, i = heapq.heappop(heap)
        try:
            nt = gs[i].send(t)
        except StopIteration:
            continue
        heapq.heappush(heap, (nt, i))
    return farm


def water_wait(farm, p, t, W, RES):
    """while not can_harvest(): if water<W and tank>RES: use_item(Water)"""
    while True:
        r = farm.ready_at(p, t)
        if r <= t: return t
        c = farm.cells[p]
        if c.w < W and farm.tank(t) > RES:
            farm.water_used += 1; c.w = min(1.0, c.w + 0.25)
            t = yield t + ACT; continue
        if c.w < W:
            nxt = (math.floor(t / WATER_DT) + 1) * WATER_DT
            r = min(r, nxt)
        t = yield t + max(6, math.ceil((r - t) / 6) * 6)


def plant_ok(farm, p, t, valid):
    """plant + reroll (harvest+plant) finche' il companion e' accettabile."""
    while True:
        comp = farm.plant(p, t)
        t = yield t + ACT + 5
        if valid(comp): return t
        farm.harvest(p, t)
        t = yield t + ACT + 1
