# Simulatore bambu' (regole da decompiled_nov6/Core/Core.Content.FarmObjectS/Bamboo.cs, Drone.cs, Growable.cs).
# Crescita: 1 blocco ogni 1/(1+4*acqua) s (meanGrowTime 1.0, deviazione 0). Resa per taglio = 128 * pezzi^2.
# Fiori: f1 = 1 + a + r, f2 = f1 + max(3, b + r), F = f2 + max(3, c + r); a,b,c in {2,3,4}; r in {0,1} fisso per cella.
import math, random

OP = 2.5e-3 / (1.5**5 * 2)
ACT = 200 * OP
YF = 128.0
EVAP = -math.log(0.99)   # ~1%/s


class Cell:
    __slots__ = ("r", "plant", "h", "fl", "idx", "growing", "tc", "bt", "prog", "ts", "w", "wt", "soil")
    def __init__(self, r):
        self.r = r; self.plant = False; self.soil = False
        self.w = 0.0; self.wt = 0.0

    def water_at(self, t):
        return self.w * math.exp(-EVAP * (t - self.wt))

    def blocktime(self, t):
        return 1.0 / (1.0 + 4.0 * self.water_at(t))

    def restart(self, t):
        self.growing = True; self.ts = t; self.bt = self.blocktime(t); self.tc = t + self.bt

    def advance(self, t, blocked_at=None):
        # blocked_at: altezza di volo del drone presente nella cella (None = nessuno)
        if not self.plant:
            return
        while self.growing and self.tc <= t:
            tt = self.tc
            self.growing = False
            self.try_grow(tt, blocked_at)

    def try_grow(self, t, blocked_at):
        if blocked_at is not None and blocked_at <= self.h:
            return
        if self.h < self.fl[2] and self.h != self.fl[self.idx]:
            self.h += 1
            self.restart(t)


class Sim:
    def __init__(self, ncells, rng, tank_rate, rmap=None):
        self.rng = rng
        self.cells = [Cell(rmap[i] if rmap else rng.randrange(2)) for i in range(ncells)]
        self.t = 0.0; self.bamboo = 0.0; self.tank_rate = tank_rate; self.used_water = 0.0
        self.pos = 0; self.flight = 1; self.nact = 0
        self.stats = {"pluck_miss": 0, "reroll": 0, "wait": 0.0}

    def tank(self):
        return int(self.t * self.tank_rate) - self.used_water

    def ops(self, n):
        self.t += n * OP

    def act(self):
        self.t += ACT + 3 * OP; self.nact += 1

    def cur(self):
        return self.cells[self.pos]

    # ---- azioni del drone ----
    def move_to(self, j):
        c = self.cur()
        self.act()
        if c.plant:
            c.advance(self.t, self.flight)
        self.pos = j
        n = self.cells[j]
        if n.plant:
            n.advance(self.t)
            self.cut(n, self.flight)
        if c.plant:
            # OnDroneLeft
            c.advance(self.t, self.flight)
            if not c.growing:
                c.try_grow(self.t, None)

    def cut(self, c, nh, collect=True):
        if nh >= c.h:
            return
        if collect:
            self.bamboo += YF * (c.h - nh) ** 2
        if nh == 0:
            c.plant = False
            return
        if nh >= c.fl[c.idx] - 1:
            c.idx = min(c.idx + 1, 2)
        else:
            c.idx = 0
            while c.idx < 2 and nh >= c.fl[c.idx]:
                c.idx += 1
        c.h = nh
        if c.growing:   # Instagrow -> bloccato dal drone
            c.growing = False
            c.try_grow(self.t, self.flight)

    def hover(self, h):
        c = self.cur()
        self.ops(3)
        if c.plant:
            c.advance(self.t, self.flight)
            if h < c.h:
                self.t += OP
                return False
        self.act()
        up = h > self.flight
        self.flight = h
        if c.plant and up:
            c.advance(self.t, self.flight)
            if not c.growing:
                c.try_grow(self.t, None)
        return True

    def measure(self):
        self.ops(2)
        c = self.cur()
        if not c.plant:
            return None
        return c.fl[c.idx] - 1

    def harvest(self):
        c = self.cur()
        self.act()
        if not c.plant:
            return
        c.advance(self.t, self.flight)
        if not c.growing:
            self.bamboo += YF * c.h ** 2
        c.plant = False
        self.flight = 1

    def till(self):
        c = self.cur(); self.act(); c.plant = False; c.soil = not c.soil; self.flight = 1

    def plant(self):
        c = self.cur(); self.act()
        if c.plant or not c.soil:
            return
        rng = self.rng
        c.plant = True; c.h = 1; c.idx = 0
        f1 = 1 + rng.randrange(2, 5) + c.r
        f2 = f1 + max(3, rng.randrange(2, 5) + c.r)
        F = f2 + max(3, rng.randrange(2, 5) + c.r)
        c.fl = [f1, f2, F]
        c.restart(self.t)

    def get_water(self):
        self.ops(2)
        return self.cur().water_at(self.t)

    def water(self, n):
        c = self.cur(); self.act()
        n = min(n, self.tank())
        if n <= 0:
            return
        self.used_water += n
        w = min(1.0, c.water_at(self.t) + 0.25 * n)
        c.w = w; c.wt = self.t
        if c.plant and c.growing:     # TryScheduleGrow: riparte con la frazione gia' fatta
            done = (self.t - c.ts) / c.bt
            c.ts = self.t; c.bt = c.blocktime(self.t)
            c.tc = self.t + c.bt * max(0.0, 1.0 - done)
            # (approssimazione: la frazione e' riferita al nuovo blocco)

    def wait_until(self, t):
        if t > self.t:
            self.stats["wait"] += t - self.t
            self.t = t
