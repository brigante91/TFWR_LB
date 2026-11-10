# Simulatore del sottosuolo per le classifiche Rice (regole dal decompilato del 6 nov).
import random, heapq
from opensimplex import OpenSimplex

OP = 2.5e-3 / (1.5**5 * 2)
ACT = 200 * OP
DIGF = 1.5**8
GROUNDS = {  # nome: (durezza, stabilita', autodistrutto accanto)
    "grass": (1, 1, True), "dirt": (1, 1, True), "clay": (2, 3, False), "rock": (2, 3, True),
    "terrace": (2, 3, False), "dry": (2, 3, False)}
GOALS = {"multi": 2000000, "single": 100000}

class World:
    def __init__(self, S, seed):
        self.S = S; self.r = random.Random(seed); self.chunks = {}
        self.depth = [[0]*S for _ in range(S)]
        self.over = {}  # (x,y,z) -> ground modificato
        self.ent = [[None]*S for _ in range(S)]   # (planted_t, ready_t) del riso
        self.water = [[0.0]*S for _ in range(S)]
        self.wt = [[0.0]*S for _ in range(S)]   # istante dell'ultimo aggiornamento (evaporazione 1%/s)
        self.rice = 0; self.t = 0.0; self.lost = 0; self.ndig = 0
        self.tank = 0.0; self.tank_t = 0.0
    def chunk(self, k):
        if k not in self.chunks:
            r = self.r; noise = OpenSimplex(r.randrange(1 << 30))
            num = r.randrange(0, 2)
            num2 = 16 - num - 1
            top = [[num + int((noise.noise2(i*0.1, j*0.1) + 1) * 0.5 * num2 * 0.5) for j in range(self.S)] for i in range(self.S)]
            self.chunks[k] = top
        return self.chunks[k]
    def ground(self, x, y, z):
        g = self.over.get((x, y, z))
        if g: return g
        k, lz = divmod(z, 16)
        if k == 0:  # NOCLAY0: in gioco il primo strato non ha argilla
            return "grass" if z == 0 else "dirt"
        c = self.chunk(k)[x][y]
        if lz < c: return "grass" if z == 0 else "dirt"
        if lz <= c + 1: return "clay"
        return "rock"
    def top(self, x, y): return self.ground(x, y, self.depth[x][y])
    def inb(self, x, y): return 0 <= x < self.S and 0 <= y < self.S
    def clear_to(self, x, y, upto):
        if self.depth[x][y] >= upto: return
        self.depth[x][y] = upto
        if self.ent[x][y] is not None:
            if self.ent[x][y][1] <= self.t: self.lost += 1
            else: self.lost += 1
        self.ent[x][y] = None
    def dig(self, x, y):
        h = GROUNDS[self.top(x, y)][0]
        ops = -(-h / OP // DIGF)
        upto = self.depth[x][y] + 1
        self.clear_to(x, y, upto)
        q = []
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            a, b = x+dx, y+dy
            if self.inb(a, b):
                if GROUNDS[self.top(a, b)][2]: self.clear_to(a, b, upto - 1)
                else: q.append((a, b))
        for dx, dy in ((1,1),(1,-1),(-1,1),(-1,-1)):
            if self.inb(x+dx, y+dy): q.append((x+dx, y+dy))
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if max(abs(dx), abs(dy)) == 2 and dx != dy and self.inb(x+dx, y+dy): q.append((x+dx, y+dy))
        while q:
            a, b = q.pop(0)
            nb = [(a+1,b),(a-1,b),(a,b+1),(a,b-1)]
            num = 0
            for c, d in nb:
                if self.inb(c, d) and self.depth[c][d] > num: num = self.depth[c][d]
            for z in range(num - 1, self.depth[a][b] - 1, -1):
                if GROUNDS[self.ground(a, b, z)][1] < num - z:
                    self.clear_to(a, b, z + 1)
                    for c, d in nb:
                        if self.inb(c, d) and self.depth[c][d] < z + 1: q.append((c, d))
                    break
        return ops * OP
    def plant(self, x, y, r):
        if self.ent[x][y] is not None or self.top(x, y) != "clay": return False
        self.over[(x, y, self.depth[x][y])] = "terrace"
        g = 6 * r.uniform(0.8, 1.2) / (1 + 4 * self.wat(x, y))
        self.ent[x][y] = [self.t, self.t + g, g]
        return True
    def grown(self, x, y):
        e = self.ent[x][y]
        if e is None or e[1] > self.t: return False
        self.over[(x, y, self.depth[x][y])] = "dry"
        return True
    def wat(self, x, y):
        dt = self.t - self.wt[x][y]
        if dt > 0:
            self.water[x][y] *= 0.99 ** dt; self.wt[x][y] = self.t
        return self.water[x][y]
    def add_water(self, x, y):
        e = self.ent[x][y]; w0 = self.wat(x, y); w1 = min(1.0, w0 + 0.25); self.water[x][y] = w1
        if e is not None and e[1] > self.t:
            e[1] = self.t + (e[1] - self.t) * (1 + 4*w0) / (1 + 4*w1)
    def fert_get(self):
        if not hasattr(self, "fert_t"): self.fert_t = 0.0; self.fert = 0.0
        self.fert += (self.t - self.fert_t) * 0.8; self.fert_t = self.t
        if self.fert >= 1: self.fert -= 1; return True
        return False
    def tank_upd(self):
        self.tank += (self.t - self.tank_t) * 25.6; self.tank_t = self.t
    def tank_get(self):
        self.tank_upd()
        if self.tank >= 1: self.tank -= 1; return True
        return False

def run(S, D, prog, seed, goal):
    w = World(S, seed); r = random.Random(seed + 7)
    gens = [prog(w, d, D, r) for d in range(D)]
    heap = [(0.0, d) for d in range(D)]
    while heap:
        t, d = heapq.heappop(heap); w.t = t
        try: dt = next(gens[d])
        except StopIteration: continue
        if w.rice >= goal: return w.t, w
        heapq.heappush(heap, (t + dt, d))
    return None, w
