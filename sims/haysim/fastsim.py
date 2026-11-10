"""Simulatore veloce della classifica Hay (32 droni, 2e9 fieno), con contabilita' delle perdite.

Stesse regole di haysim.py (lette dall'IL): azioni 200 tick, 6075 tick/s, erba 3037.5/(1+4w) tick,
companion tipo uniforme {bush, carrot, tree}, posizione uniforme sul rombo di raggio 3,
acqua +0.25 per use_item, serbatoio +1 ogni 237.3 tick partendo da 0, decadimento ~1%/s.
Il fertilizzante dimezza la resa (weird), quindi non si usa.
"""
import heapq, math, random, statistics

TPS = 6075.0
ACT = 200
GROW = 3037.5
GOAL = 2_000_000_000
YIELD = 81920
WATER_DT = TPS * 20 / 512
S = 32
DECAY = 0.1 * math.log(0.99) / 607.5     # per tick, in media
DIAMOND = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4)
           if (dx or dy) and abs(dx) + abs(dy) <= 3]
SPIN = 6     # tick per giro del while di attesa
CHECK = 4    # tick di codice per reroll


def dist(a, b):
    dx = (b[0] - a[0]) % S
    dy = (b[1] - a[1]) % S
    return min(dx, S - dx) + min(dy, S - dy)


class Cell:
    __slots__ = ("w", "prog", "t", "comp")

    def __init__(self):
        self.w, self.prog, self.t, self.comp = 0.0, 1.0, 0.0, None

    def update(self, now):
        dt = now - self.t
        if dt > 0:
            w1 = self.w * math.exp(DECAY * dt)
            if self.prog < 1:
                self.prog = min(1.0, self.prog + dt * (1 + 2 * (self.w + w1)) / GROW)
            self.w, self.t = w1, now

    def ready_at(self, now):
        self.update(now)
        if self.prog >= 1:
            return now
        return now + (1 - self.prog) * GROW / (1 + 4 * self.w)


class Farm:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.bush = set()
        self.grass = {}
        self.hay = 0
        self.water_used = 0
        self.end = None
        self.stats = {"setup": 0, "yield": 0, "reroll": 0, "move": 0, "water": 0, "wait": 0}

    def tank(self, t):
        return int(t / WATER_DT) - self.water_used

    def roll(self, pos):
        kind = self.rng.randrange(3)
        dx, dy = DIAMOND[self.rng.randrange(24)]
        return kind, ((pos[0] + dx) % S, (pos[1] + dy) % S)


class Done(Exception):
    pass


def wait_grow(f, cell, t, W, RES):
    st = f.stats
    while True:
        r = cell.ready_at(t)
        if r <= t:
            return t
        if cell.w < W and f.tank(t) > RES:
            f.water_used += 1
            cell.w = min(1.0, cell.w + 0.25)
            st["water"] += ACT
            t = yield t + ACT
            continue
        if cell.w < W:
            t2 = min(r, (math.floor(t / WATER_DT) + 1) * WATER_DT)
        else:
            t2 = r
        d = max(SPIN, math.ceil((t2 - t) / SPIN) * SPIN)
        st["wait"] += d
        t = yield t + d


def harvest_until_ok(f, cell, pos, avoid, t, main):
    st = f.stats
    first = True
    while True:
        cell.update(t)
        if cell.prog >= 1 and cell.comp is not None and cell.comp[0] == 0 and cell.comp[1] in f.bush:
            f.hay += YIELD
        st["yield" if first else "reroll"] += ACT + CHECK
        first = False
        cell.prog, cell.t = 0.0, t
        cell.comp = f.roll(pos)
        t = yield t + ACT + CHECK
        if main and f.hay >= GOAL:
            f.end = t
            raise Done
        if cell.comp[0] == 0 and cell.comp[1] != avoid:
            return t


def loop2(f, a, b, t, W, RES, main):
    """Ciclo a due celle d'erba adiacenti (a, b)."""
    ca = f.grass.setdefault(a, Cell())
    cb = f.grass.setdefault(b, Cell())
    st = f.stats
    while True:
        t = yield from wait_grow(f, ca, t, W, RES)
        t = yield from harvest_until_ok(f, ca, a, b, t, main)
        st["move"] += ACT
        t = yield t + ACT
        t = yield from wait_grow(f, cb, t, W, RES)
        t = yield from harvest_until_ok(f, cb, b, a, t, main)
        st["move"] += ACT
        t = yield t + ACT + 1


def run(make_drones, seed=0, **kw):
    f = Farm(seed)
    gens = make_drones(f, **kw)
    heap = []
    for i, (t0, g) in enumerate(gens):
        next(g)
        heap.append((t0, i))
    gens = [g for _, g in gens]
    heapq.heapify(heap)
    while heap:
        t, i = heapq.heappop(heap)
        try:
            nt = gens[i].send(t)
        except (StopIteration, Done):
            if f.end is not None:
                break
            continue
        heapq.heappush(heap, (nt, i))
    return f


def evaluate(make_drones, n=6, **kw):
    fs = [run(make_drones, seed=s, **kw) for s in range(n)]
    times = [x.end / TPS for x in fs]
    tot = {k: statistics.mean(x.stats[k] for x in fs) / TPS / 32 for k in fs[0].stats}
    return statistics.mean(times), min(times), max(times), tot


# ---------------------------------------------------------------- strategia attuale
def block_origin(b):
    i = b % 8
    return 4 * i, (8 * (b // 8) + 4 * (i % 2)) % S


def spawn_tree(n):
    start = {}
    def rr(lo, hi, t):
        while hi - lo > 1:
            mid = (lo + hi) // 2
            t += ACT
            rr(mid, hi, t)
            hi = mid
        start[lo] = t
    rr(0, n, 0)
    return start


def base_drone(f, b, W, RES):
    t = yield
    st = f.stats
    t0 = t
    bx, by = block_origin(b)
    t = yield t + dist((0, 0), (bx, (by + 7) % S)) * ACT
    x, y = bx, (by + 7) % S
    for k in range(7):
        d = 1 if k % 2 == 0 else -1
        for j in range(4):
            f.bush.add((x % S, y)); t = yield t + ACT
            if j < 3:
                x += d; t = yield t + ACT
        y = (y - 1) % S; t = yield t + ACT
    for _ in range(2):
        f.bush.add((x % S, y)); t = yield t + ACT
        x -= 1; t = yield t + ACT
    st["setup"] += t - t0
    # il drone parte sulla cella ovest... in realta' (bx, by) dopo due West dalla (bx+2)
    yield from loop2(f, (bx, by), (bx + 1, by), t, W, RES, b == 0)


def baseline(f, W=0.68, RES=16):
    starts = spawn_tree(32)
    return [(starts[b] + ACT, base_drone(f, b, W, RES)) for b in range(32)]


if __name__ == "__main__":
    import time
    t = time.time()
    print("baseline", evaluate(baseline, n=4), round(time.time() - t, 1), "s")
