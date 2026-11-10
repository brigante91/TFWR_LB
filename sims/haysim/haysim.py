"""Simulatore della leaderboard Hay (32 droni, 2e9 fieno) con le regole lette dall'IL.

Tempo in tick (6075 tick = 1 s simulato). Azioni 200 tick, codice ~1 tick per operazione.
Erba: cresce in 3037.5/(1+4w) tick, deterministica. Acqua: +0.25 per use_item,
decadimento 0.99 con prob. 0.1 ogni 607.5 tick. Serbatoio: +1 ogni 237.3 tick (20/2^9 s).
Fertilizzante: +1 ogni 1.25 s, matura l'erba subito. Companion: tipo uniforme su
{bush, carrot, tree}, posizione uniforme sul rombo di raggio 3 (24 celle).
"""
import heapq, random, math

TPS = 6075.0
ACT = 200
GROW = 3037.5
GOAL = 2_000_000_000
YIELD = 81920
WATER_DT = TPS * 20 / 512
FERT_DT = TPS * 20 / 16
S = 32
DIAMOND = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4)
           if (dx or dy) and abs(dx) + abs(dy) <= 3]


class Cell:
    __slots__ = ("w", "prog", "t", "comp")

    def __init__(self):
        self.w = 0.0
        self.prog = 1.0   # erba iniziale matura
        self.t = 0.0
        self.comp = None

    def update(self, now):
        dt = now - self.t
        if dt > 0:
            # decadimento medio continuo dell'acqua
            k = 0.1 * math.log(0.99) / 607.5
            w0 = self.w
            w1 = w0 * math.exp(k * dt)
            wavg = (w0 + w1) / 2
            self.prog = min(1.0, self.prog + dt * (1 + 4 * wavg) / GROW)
            self.w = w1
            self.t = now

    def ready_at(self, now):
        self.update(now)
        if self.prog >= 1:
            return now
        return now + (1 - self.prog) * GROW / (1 + 4 * self.w)


class Farm:
    def __init__(self, rng):
        self.rng = rng
        self.grass = {}
        self.bush = set()
        self.hay = 0
        self.t_goal = None

    def tank(self, now):
        return int(now / WATER_DT) - self.water_used

    def fert(self, now):
        return int(now / FERT_DT) - self.fert_used

    def roll(self, pos):
        rs = self.__dict__.setdefault('_rngs', {})
        r = rs.get(pos)
        if r is None:
            r = rs[pos] = random.Random(hash((self.seed0, pos)))
        kind = r.randrange(3)  # 0 = bush
        dx, dy = DIAMOND[r.randrange(24)]
        return kind, ((pos[0] + dx) % S, (pos[1] + dy) % S)

    def valid(self, comp):
        return comp[0] == 0 and comp[1] in self.bush


def run(strategy, seed=0, **kw):
    rng = random.Random(seed)
    farm = Farm(rng)
    farm.seed0 = seed
    farm.water_used = 0
    farm.fert_used = 0
    gens = strategy(farm, **kw)
    heap = [(t, i) for i, (t, g) in enumerate(gens)]
    gens = [g for _, g in gens]
    for g in gens:
        next(g)
    heapq.heapify(heap)
    last = 0
    while heap:
        t, i = heapq.heappop(heap)
        try:
            nt = gens[i].send(t)
        except StopIteration:
            last = max(last, t)
            continue
        heapq.heappush(heap, (nt, i))
    return last / TPS, farm
