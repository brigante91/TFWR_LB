"""Simulatore della classifica Sunflowers_Single (1 drone, campo 8x8, 10.000 power).

Stesse regole di sunsim2.py (tarate sui test in gioco del 7 nov 2026):
  - crescita 7 s * U[0.8,1.2] / (1 + 4*acqua), acqua della cella con decadimento medio ~1%/s,
    ricalcolo della crescita quando l'acqua cambia (asset: meanGrowTime 7.0, dev 0.2);
  - petali U{7..15} a ogni plant; harvest: boost se petali == massimo del campo (semi compresi)
    e >= 10 girasoli; flag globale = !boost, un raccolto dopo un flag sporco perde il bonus;
  - serbatoio +1 ogni 20/512 s da t=0; use_item(Water,n) fallisce (1 tick) se < n;
  - power 0 all'inizio: 3037.5 tick/s fino al primo raccolto con resa, poi 6075;
    UsePower ogni 0.2 s toglie ops/6000 (1 drone);
  - costi: azione 200 (1 se fallisce), measure/get_* /can_harvest/num_items 1, codice ~1 per
    operazione (moltiplicatore K per la taratura), get_time 0.
Un drone solo: niente scheduler, il tempo avanza col contatore di tick del drone.
"""
import math, random

TPS = 6075.0
GROW = 7.0
DEV = 0.2
LAM = -math.log(0.99)
TANK_DT = 20.0 / 512
N = 8
DIRS = {'E': (1, 0), 'W': (-1, 0), 'N': (0, 1), 'S': (0, -1)}


class Done(Exception):
    pass


class SW:
    def __init__(self, seed, goal=10000, K=1.0, maxt=1500.0):
        self.rv = random.Random(seed * 7919 + 1)
        self.rr = random.Random(seed * 7919 + 2)
        self.goal = goal
        self.K = K
        self.maxt = maxt
        n = N * N
        self.val = [0] * n
        self.grass = [True] * n
        self.soil = [False] * n
        self.prog = [0.0] * n
        self.rf = [1.0] * n
        self.w = [0.0] * n
        self.tw = [0.0] * n
        self.tl = [0.0] * n
        self.cnt = [0] * 17
        self.nsun = 0
        self.flag = False
        self.power = 0.0
        self.t = 0.0
        self.tps = TPS / 2
        self.next_use = 0.2
        self.used = 0.0
        self.tank_used = 0
        self.x = 0
        self.y = 0
        self.nboost = self.nplain = self.nzero = self.nlost = self.nreroll = 0
        self.nwater = 0
        self.nmove = 0
        self.ended = None
        self.twait = 0.0

    # ---- tempo ----
    def spend(self, ticks):
        # avanza di `ticks` tick del drone, processando UsePower
        while ticks > 0:
            dt_end = (self.next_use - self.t) * self.tps
            if ticks < dt_end:
                self.t += ticks / self.tps
                self.used += ticks / 6000.0
                return
            self.t = self.next_use
            self.used += dt_end / 6000.0
            ticks -= dt_end
            if self.power > 0:
                self.power -= self.used
                if self.power <= 0:
                    self.power = 0.0
                    self.tps = TPS / 2
            self.used = 0.0
            self.next_use += 0.2
            if self.t > self.maxt:
                raise Done()

    def code(self, ops):
        self.codet = getattr(self, 'codet', 0) + ops * self.K
        self.spend(ops * self.K)

    # ---- campo ----
    def c(self):
        return self.y * N + self.x

    def water_now(self, c):
        return self.w[c] * math.exp(-LAM * (self.t - self.tw[c]))

    def _upd(self, c):
        t = self.t
        if self.val[c]:
            dt = t - self.tl[c]
            if dt > 0 and self.prog[c] < 1.0:
                w0 = self.water_now_at(c, self.tl[c])
                integ = dt + 4.0 * w0 * (1 - math.exp(-LAM * dt)) / LAM
                self.prog[c] = min(1.0, self.prog[c] + integ / (GROW * self.rf[c]))
            self.tl[c] = t
        self.w[c] = self.water_now(c)
        self.tw[c] = t

    def water_now_at(self, c, t):
        return self.w[c] * math.exp(-LAM * (t - self.tw[c]))

    def grown(self, c):
        self._upd(c)
        return self.prog[c] >= 1.0 - 1e-12

    def grow_eta(self, c):
        # secondi che mancano alla crescita (stima con acqua costante al valore attuale)
        self._upd(c)
        if self.prog[c] >= 1.0:
            return 0.0
        return (1.0 - self.prog[c]) * GROW * self.rf[c] / (1 + 4 * self.w[c])

    # ---- azioni (ritornano come le funzioni del gioco) ----
    def move(self, d):
        dx, dy = DIRS[d]
        self.x = (self.x + dx) % N
        self.y = (self.y + dy) % N
        self.nmove += 1
        self.spend(200)

    def till(self):
        c = self.c()
        self.grass[c] = False
        self.soil[c] = True
        if self.val[c]:
            self.cnt[self.val[c]] -= 1
            self.nsun -= 1
            self.val[c] = 0
        self.spend(200)

    def ground_soil(self):
        self.spend(1)
        return self.soil[self.c()]

    def entity(self):
        self.spend(1)
        c = self.c()
        if self.val[c]:
            return 'sun'
        if self.grass[c]:
            return 'grass'
        return None

    def plant(self):
        c = self.c()
        if self.val[c] or not self.soil[c]:
            self.spend(1)
            return False
        self._upd(c)
        v = self.rv.randint(7, 15)
        self.val[c] = v
        self.prog[c] = 0.0
        self.rf[c] = 1.0 - DEV + 2 * DEV * self.rr.random()
        self.tl[c] = self.t
        self.cnt[v] += 1
        self.nsun += 1
        self.spend(200)
        return True

    def measure(self):
        self.spend(1)
        return self.val[self.c()] or None

    def get_water(self):
        self.spend(1)
        return self.water_now(self.c())

    def use_water(self, n=1):
        if n < 1 or int(self.t / TANK_DT) - self.tank_used < n:
            self.spend(1)
            return False
        c = self.c()
        self._upd(c)
        self.w[c] = min(1.0, self.w[c] + 0.25 * n)
        self.tank_used += n
        self.nwater += 1
        self.spend(200)
        return True

    def can_harvest(self):
        self.spend(1)
        c = self.c()
        return bool(self.val[c]) and self.grown(c)

    def num_power(self):
        self.spend(1)
        return self.power

    def harvest(self):
        c = self.c()
        v = self.val[c]
        if not v:
            if self.grass[c]:
                self.grass[c] = False
                self.spend(200)
                return True
            self.spend(1)
            return False
        g = self.grown(c)
        mx = 15
        while mx > 7 and self.cnt[mx] == 0:
            mx -= 1
        boost = (v == mx) and self.nsun >= 10
        had = self.flag
        self.flag = not boost
        if had:
            if boost and g:
                self.nlost += 1
            boost = False
        self.val[c] = 0
        self.cnt[v] -= 1
        self.nsun -= 1
        if g:
            amt = 8.0 if boost else 1.0
            if boost:
                self.nboost += 1
            else:
                self.nplain += 1
            if self.power == 0.0:
                self.used = 0.0
                self.tps = TPS
            self.power += amt
        else:
            self.nzero += 1
        self.spend(200)
        return True

    def clear(self):
        # la run finisce quando il programma ritorna dopo clear() (200 tick)
        self.spend(200)
        self.ended = (self.t, self.power >= self.goal)
        raise Done()

    def wait_grown(self, iter_ops=2):
        # while not can_harvest(): pass  -> avanza fino alla crescita a passi brevi
        c = self.c()
        t0 = self.t
        while True:
            if self.can_harvest():
                self.twait += self.t - t0
                return
            eta = self.grow_eta(c)
            self.spend(max(iter_ops, min(eta * self.tps, 0.02 * self.tps)) * 1.0)

    def max_field(self):
        mx = 15
        while mx > 7 and self.cnt[mx] == 0:
            mx -= 1
        return mx if self.cnt[mx] else 0


def run(prog, seed, P, K=1.0):
    w = SW(seed, K=K)
    try:
        prog(w, P)
    except Done:
        pass
    if w.ended is None:
        w.ended = (w.t, w.power >= w.goal)
    return dict(t=w.ended[0], ok=w.ended[1], boost=w.nboost, plain=w.nplain, zero=w.nzero,
                lost=w.nlost, water=w.nwater, moves=w.nmove, tank=w.tank_used, wait=w.twait, reroll=w.nreroll)


# ===========================================================================
# v1 (script dell'utente, 5:23.470 in gioco)
# ===========================================================================
SWEEP = (['E'] * 7 + ['N'] + ['W'] * 7 + ['N']) * 4


def goto(w, tx, ty):
    w.code(1 + 3 + 3)
    dx = (tx - w.x) % N
    if dx <= N // 2:
        w.code(1)
        for _ in range(dx):
            w.code(1)
            w.move('E')
    else:
        w.code(1)
        for _ in range(N - dx):
            w.code(1)
            w.move('W')
    w.code(3 + 3)
    dy = (ty - w.y) % N
    if dy <= N // 2:
        w.code(1)
        for _ in range(dy):
            w.code(1)
            w.move('N')
    else:
        w.code(1)
        for _ in range(N - dy):
            w.code(1)
            w.move('S')


def prog_v1(w, P):
    STOP = w.goal + 5
    MAXH = 64 - 10
    first = True
    w.code(2)
    while True:
        buckets = [[] for _ in range(9)]
        w.code(1 + 9)
        for step in SWEEP:
            w.code(1 + 1)
            if first:
                w.code(2)
                if not w.ground_soil():
                    w.till()
            w.code(2)
            if w.entity() is None:
                w.plant()
            v = w.measure()
            w.code(2)
            if w.get_water() < P.get('WT', 0.75):
                w.use_water(P.get('WN', 1))
            w.code(1 + 1 + 1 + 1 + 2 + 1)        # buckets[v-7].append((x, y))
            buckets[v - 7].append((w.x, w.y))
            w.move(step)
        first = False
        collected = 0
        v = 15
        w.code(3)
        while v >= 7:
            w.code(1 + 3)
            cells = buckets[v - 7]
            n = len(cells)
            if n > 0:
                w.code(2 + 2 + 2 + 2 + 20 + 2)
                cx, cy = w.x, w.y
                da = min((cells[0][0] - cx) % N, (cx - cells[0][0]) % N) + min((cells[0][1] - cy) % N, (cy - cells[0][1]) % N)
                db = min((cells[-1][0] - cx) % N, (cx - cells[-1][0]) % N) + min((cells[-1][1] - cy) % N, (cy - cells[-1][1]) % N)
                seq = cells if da <= db else cells[::-1]
                for pos in seq:
                    w.code(1 + 2 + 2)
                    if collected >= MAXH:
                        break
                    goto(w, pos[0], pos[1])
                    w.code(1)
                    w.wait_grown()
                    w.harvest()
                    collected += 1
                    w.code(1 + 2)
                    if w.num_power() >= STOP:
                        w.code(2)
                        w.clear()
            w.code(2)
            if collected >= MAXH:
                break
            v -= 1
            w.code(1)


# ===========================================================================
# v2: discesa con ripianto
# ===========================================================================

def tdist(a, b):
    ax, ay = a % N, a // N
    bx, by = b % N, b // N
    dx = abs(ax - bx); dy = abs(ay - by)
    return min(dx, N - dx) + min(dy, N - dy)


def goto_c(w, c):
    # goto con il giro toroidale piu' corto
    tx, ty = c % N, c // N
    w.code(1 + 6)
    dx = (tx - w.x) % N
    if dx <= N // 2:
        for _ in range(dx):
            w.code(1); w.move('E')
    else:
        for _ in range(N - dx):
            w.code(1); w.move('W')
    w.code(6)
    dy = (ty - w.y) % N
    if dy <= N // 2:
        for _ in range(dy):
            w.code(1); w.move('N')
    else:
        for _ in range(N - dy):
            w.code(1); w.move('S')


def water_fill(w, P):
    if P.get('WT') is None:
        return
    g = w.get_water()
    w.code(2)
    if g < P['WT']:
        n = int((1.0 - g) * 4 + 0.999)
        w.code(4)
        if n > 0:
            w.use_water(min(n, 4))


def prog_v2(w, P):
    STOP = w.goal + 5
    RL = P.get('RL', 11)          # ripianta subito se il livello corrente e' >= RL
    BUF = P.get('BUF', 10)
    vals = [0] * 64
    first = True
    w.code(5)
    while True:
        # ---- semina delle celle vuote: serpentina completa (1 mossa per cella) ----
        empties = [c for c in range(64) if vals[c] == 0]
        w.code(3 + 64 * 3)
        if first or len(empties) > P.get('SNAKE_MIN', 20):
            # serpentina fissa da (0,0): va prima a (0,0)
            goto_c(w, 0)
            for i, step in enumerate(SWEEP):
                c = w.c()
                w.code(4)
                if first:
                    w.code(2)
                    if not w.ground_soil():
                        w.till()
                w.code(2)
                if vals[c] == 0:
                    w.plant()
                    vals[c] = w.measure()
                    w.code(3)
                    water_fill(w, P)
                elif P.get('WT') is not None and P.get('WALL'):
                    water_fill(w, P)
                if i < 63:
                    w.move(step)
        else:
            # poche vuote: giro al piu' vicino
            todo = list(empties)
            while todo:
                w.code(2 + len(todo) * 10)
                c0 = w.c()
                j = min(range(len(todo)), key=lambda q: tdist(c0, todo[q]))
                c = todo.pop(j)
                goto_c(w, c)
                w.plant()
                vals[c] = w.measure()
                w.code(3)
                water_fill(w, P)
        first = False
        # ---- discesa: raccogli sempre il massimo, il piu' vicino ----
        nsun = sum(1 for v in vals if v)
        while nsun >= BUF:
            M = max(vals)
            cand = [c for c in range(64) if vals[c] == M]
            w.code(64 * 3 + len(cand) * 12)     # trova il massimo e il piu' vicino
            c0 = w.c()
            c = min(cand, key=lambda q: (tdist(c0, q)))
            goto_c(w, c)
            w.code(1)
            w.wait_grown()
            w.harvest()
            vals[c] = 0
            nsun -= 1
            w.code(3)
            if w.num_power() >= STOP:
                w.clear()
            # ripianto immediato se il livello e' alto
            w.code(2)
            if M >= RL:
                Ma = max(vals)
                w.code(64 * 2)
                w.plant()
                u = w.measure()
                w.code(2)
                while u > Ma and Ma > 0:
                    w.code(2)
                    w.harvest()          # il seme e' il massimo: flag pulito
                    w.nreroll += 1
                    w.plant()
                    u = w.measure()
                vals[c] = u
                nsun += 1
                water_fill(w, P)


def prog_v3(w, P):
    """Discesa per livelli con liste per valore (costi realistici).
    P: WT soglia acqua (riempi fino a 1), NN=1 giro al piu' vicino nel livello (altrimenti
    lista dall'estremo piu' vicino), MINV valore minimo accettato in semina (reroll sotto),
    HMAX raccolti per ciclo (55 = fino a 10 girasoli in campo compreso quello raccolto)."""
    STOP = w.goal + P.get('MARGIN', 5)
    MINV = P.get('MINV', 7)
    HMAX = P.get('HMAX', 54)
    NN = P.get('NN', 1)
    first = True
    vals = [0] * 64
    w.code(5)
    while True:
        buckets = [[] for _ in range(16)]
        w.code(16)
        # ---- semina a serpentina (64 mosse, come la v1) ----
        for step in SWEEP:
            c = w.c()
            w.code(2)
            if first:
                w.code(2)
                if not w.ground_soil():
                    w.till()
            w.code(2)
            if vals[c] == 0:
                w.plant()
                v = w.measure()
                w.code(2)
                while v < MINV:
                    w.code(2)
                    w.harvest()
                    w.nreroll += 1
                    w.plant()
                    v = w.measure()
                vals[c] = v
                w.code(1)
                water_fill(w, P)
            elif P.get('WALL'):
                water_fill(w, P)
            buckets[vals[c]].append(c)
            w.code(4)
            w.move(step)
        first = False
        # ---- discesa ----
        got = 0
        lvl = 15
        w.code(3)
        while got < HMAX and lvl >= 7:
            L = buckets[lvl]
            w.code(4)
            while L and got < HMAX:
                c0 = w.c()
                if NN:
                    w.code(5 + 17 * len(L))
                    j = min(range(len(L)), key=lambda q: tdist(c0, L[q]))
                    if P.get('GF'):
                        w.code(len(L) * 3)
                        gr = [q for q in range(len(L)) if w.val[L[q]] and w.grown(L[q])]
                        if gr:
                            j = min(gr, key=lambda q: tdist(c0, L[q]))
                else:
                    w.code(16)
                    j = 0 if tdist(c0, L[0]) <= tdist(c0, L[-1]) else len(L) - 1
                c = L.pop(j)
                goto_c(w, c)
                w.code(2)
                if P.get('WW'):
                    w.code(2)
                    if not w.can_harvest():
                        g = w.get_water()
                        if g < 0.99:
                            w.use_water(min(4, int((1 - g) * 4 + 0.999)))
                w.wait_grown()
                w.harvest()
                vals[c] = 0
                got += 1
                w.code(3)
                if w.num_power() >= STOP:
                    w.clear()
            lvl -= 1


def sweep_n():
    # serpentina n x n con ritorno toroidale (copre tutte le celle da qualunque partenza)
    return (['E'] * (N - 1) + ['N'] + ['W'] * (N - 1) + ['N']) * (N // 2) + ((['E'] * (N - 1) + ['N']) if N % 2 else [])


def prog_v4(w, P):
    """Discesa con ripianto immediato (idea del reroll gratuito).
    Dopo il raccolto di una cella al livello L si ripianta subito:
      u > massimo rimasto      -> reroll gratuito (il seme e' il massimo: flag pulito)
      L-G < u <= massimo        -> DIRTY=1: reroll (sporca il flag se u < massimo);
                                   DIRTY=0: tenuto nella lista u (si aspetta la crescita)
      u <= L-G                  -> tenuto, raccolto in questo ciclo al livello u
    Sotto il livello RL non si ripianta: le celle restano vuote e si riseminano quando nel campo
    restano BUF girasoli (serpentina se le vuote sono > SNAKE_MIN, altrimenti giro al piu' vicino).
    Acqua: alla semina/ripianto, se < WT riempi fino a 1."""
    STOP = w.goal + 5
    G = P.get('G', 3)
    RL = P.get('RL', 11)
    BUF = P.get('BUF', 10)
    DIRTY = P.get('DIRTY', 1)
    if P.get('WS'):
        w.spend(200)                    # set_world_size(n)
    vals = [0] * (N * N)
    est = [0.0] * (N * N)
    buckets = [[] for _ in range(16)]
    first = True
    w.code(10)
    while True:
        # ---- semina delle vuote ----
        empties = [c for c in range(N * N) if vals[c] == 0]
        if not first and P.get('END') is not None:
            # ultimo ciclo: semina solo i raccolti che mancano (+ margine)
            need = int((STOP - w.power) / 7.8) + P['END']
            w.code(8)
            if need < len(empties):
                keep = []
                c0 = w.c()
                rest = list(empties)
                while rest and len(keep) < need:
                    j = min(range(len(rest)), key=lambda q: tdist(c0, rest[q]))
                    keep.append(rest.pop(j)); c0 = keep[-1]
                empties = keep
                w.endcut = True
        if first or len(empties) > P.get('SNAKE_MIN', 30):
            nplanted = 0
            SWEEP_I = [-1]
            for step in sweep_n():
                SWEEP_I[0] += 1
                c = w.c()
                if first and P.get('BOOT') and w.power == 0 and nplanted >= 10:
                    # avvio: raccogli un massimo gia' cresciuto vicino per avere power (velocita' piena)
                    mx = 15
                    while mx > 7 and not buckets[mx]:
                        mx -= 1
                    w.code(8 + 3 * (15 - mx) + 6 * len(buckets[mx]))
                    rd = [q for q in buckets[mx] if est[q] <= w.t and tdist(c, q) <= P['BOOT']]
                    if rd:
                        q = min(rd, key=lambda r: tdist(c, r))
                        goto_c(w, q)
                        w.code(2)
                        w.wait_grown()
                        w.harvest()
                        buckets[mx].remove(q)
                        vals[q] = 0
                        nsun_boot = True
                        goto_c(w, c)
                w.code(3)
                if first:
                    w.code(2)
                    if not w.ground_soil():
                        w.till()
                w.code(2)
                if vals[c] == 0:
                    w.plant()
                    v = w.measure()
                    if P.get('LATE15') is not None and SWEEP_I[0] > P['LATE15']:
                        w.code(3)
                        while v == 15:
                            w.code(2)
                            w.harvest(); w.nreroll += 1; w.plant(); v = w.measure()
                    vals[c] = v
                    buckets[v].append(c)
                    nplanted += 1
                    w.code(4)
                    water_fill(w, P)
                    if P.get('FB1') and w.water_now(c) < 0.2:
                        w.code(3)
                        w.use_water(1)
                    est[c] = w.t + 8.4 / (1 + 4 * w.water_now(c)); w.code(6)
                w.move(step)
        else:
            todo = list(empties)
            w.code(70)
            while todo:
                c0 = w.c()
                w.code(5 + 17 * len(todo))
                j = min(range(len(todo)), key=lambda q: tdist(c0, todo[q]))
                c = todo.pop(j)
                goto_c(w, c)
                w.plant()
                v = w.measure()
                vals[c] = v
                buckets[v].append(c)
                w.code(4)
                water_fill(w, P)
                est[c] = w.t + 8.4 / (1 + 4 * w.water_now(c)); w.code(6)
        first = False
        # ---- discesa con ripianto ----
        nsun = sum(1 for v in vals if v)
        lvl = 15
        w.code(3)
        while nsun >= BUF and lvl >= 7:
            L = buckets[lvl]
            w.code(4)
            if not L:
                lvl -= 1
                continue
            c0 = w.c()
            if P.get('NNC'):
                w.code(6 + P['NNC'] * len(L))     # un solo passaggio, tabelle precalcolate
            else:
                w.code(5 + 17 * len(L))
            j = min(range(len(L)), key=lambda q: tdist(c0, L[q]))
            if P.get('LA'):
                nxt = []
                m2 = lvl - 1
                while m2 >= 7 and not buckets[m2]:
                    m2 -= 1
                if len(L) == 1 and m2 >= 7:
                    nxt = buckets[m2]
                others = lambda q: [L[r] for r in range(len(L)) if r != q] or nxt
                def score(q):
                    o = others(q)
                    return tdist(c0, L[q]) + P['LA'] * (min(tdist(L[q], r) for r in o) if o else 0)
                j = min(range(len(L)), key=score)
            if P.get('GF'):
                if not P.get('NNC'):
                    w.code(len(L) * 3)
                if P['GF'] == 2:
                    gr = [q for q in range(len(L)) if est[L[q]] <= w.t]
                else:
                    gr = [q for q in range(len(L)) if w.val[L[q]] and w.grown(L[q])]
                if gr:
                    j = min(gr, key=lambda q: tdist(c0, L[q]))
            c = L.pop(j)
            goto_c(w, c)
            w.code(2)
            if P.get('WW'):
                w.code(2)
                if not w.can_harvest():
                    g = w.get_water()
                    if g < 0.99:
                        w.use_water(min(4, int((1 - g) * 4 + 0.999)))
            w.wait_grown()
            w.harvest()
            vals[c] = 0
            nsun -= 1
            w.code(3)
            if w.num_power() >= STOP:
                w.clear()
            w.code(2)
            if lvl >= RL:
                # massimo rimasto: il livello corrente se la lista non e' vuota, altrimenti sotto
                mx = lvl
                while mx >= 7 and not buckets[mx]:
                    mx -= 1
                w.code(4 + 3 * (lvl - mx))
                if P.get('MXRULE') and mx < RL:
                    continue
                w.plant()
                u = w.measure()
                REROLLS = [0]
                w.code(2)
                while True:
                    w.code(4)
                    if P.get('MXRULE'):
                        if u >= mx:
                            w.harvest(); w.nreroll += 1
                            nrr = locals().get('nrr', 0)
                            if P.get('MAXRR') is not None and REROLLS[0] >= P['MAXRR']:
                                u = None
                                break
                            REROLLS[0] += 1
                            w.plant(); u = w.measure()
                            continue
                        break
                    if u > mx or (DIRTY and u > lvl - G):
                        w.harvest()
                        w.nreroll += 1
                        w.plant()
                        u = w.measure()
                        continue
                    break
                if u is None:
                    # cella lasciata vuota: verra' seminata nel ciclo dopo
                    w.code(2)
                    continue
                vals[c] = u
                buckets[u].append(c)
                nsun += 1
                w.code(3)
                if P.get('MXRULE') and u == mx - 1:
                    water_fill(w, dict(P, WT=0.85))
                else:
                    water_fill(w, P)
                est[c] = w.t + 8.4 / (1 + 4 * w.water_now(c)); w.code(6)


def prog_cont(w, P):
    """Schema continuo: niente cicli. Prima semina a serpentina (con avvio BOOT), poi sempre:
    vai alla cella piu' vicina col valore massimo del campo (preferendo quelle stimate cresciute),
    raccogli, ripianta subito; se il seme nuovo supera il massimo rimasto lo rilanci (gratis:
    e' il massimo) finche' il massimo rimasto e' >= TH; sotto TH lo tieni (diventa il massimo).
    Acqua alla semina se < WT, fino a 1 prima di aspettare (WW)."""
    STOP = w.goal + 5
    TH = P.get('TH', 11)
    NNC = P.get('NNC', 10)
    vals = [0] * 64
    est = [0.0] * 64
    buckets = [[] for _ in range(16)]
    w.code(10)
    nplanted = 0
    for step in SWEEP:
        c = w.c()
        if P.get('BOOT') and w.power == 0 and nplanted >= 10:
            mx = 15
            while mx > 7 and not buckets[mx]:
                mx -= 1
            w.code(8 + NNC * len(buckets[mx]))
            rd = [q for q in buckets[mx] if est[q] <= w.t and tdist(c, q) <= P['BOOT']]
            if rd:
                q = min(rd, key=lambda r: tdist(c, r))
                goto_c(w, q); w.wait_grown(); w.harvest()
                buckets[mx].remove(q); vals[q] = 0
                goto_c(w, c)
        w.code(5)
        if not w.ground_soil():
            w.till()
        w.plant(); v = w.measure(); vals[c] = v; buckets[v].append(c); nplanted += 1
        w.code(4); water_fill(w, P)
        est[c] = w.t + 8.4 / (1 + 4 * w.water_now(c)); w.code(6)
        w.move(step)
    # empties lasciate dal boot: piantale subito al passaggio (semplice: giro al piu' vicino)
    for c in range(64):
        if vals[c] == 0:
            goto_c(w, c); w.plant(); v = w.measure(); vals[c] = v; buckets[v].append(c)
            water_fill(w, P); est[c] = w.t + 8.4 / (1 + 4 * w.water_now(c))
    while True:
        M = 15
        while M > 7 and not buckets[M]:
            M -= 1
        L = buckets[M]
        c0 = w.c()
        w.code(8 + 2 * (15 - M) + NNC * len(L))
        gr = [q for q in range(len(L)) if est[L[q]] <= w.t]
        pool = gr if gr else range(len(L))
        j = min(pool, key=lambda q: tdist(c0, L[q]))
        c = L.pop(j)
        goto_c(w, c)
        if P.get('WW'):
            w.code(2)
            if not w.can_harvest():
                g = w.get_water()
                if g < 0.99:
                    w.use_water(min(4, int((1 - g) * 4 + 0.999)))
        w.wait_grown()
        w.harvest()
        vals[c] = 0
        w.code(3)
        if w.num_power() >= STOP:
            w.clear()
        Ma = M
        while Ma >= 7 and not buckets[Ma]:
            Ma -= 1
        w.code(4 + 2 * (M - max(Ma, 7)))
        w.plant(); u = w.measure()
        w.code(2)
        while u > Ma and Ma >= TH:
            w.code(3)
            w.harvest(); w.nreroll += 1; w.plant(); u = w.measure()
        vals[c] = u; buckets[u].append(c)
        w.code(4); water_fill(w, P)
        est[c] = w.t + 8.4 / (1 + 4 * w.water_now(c)); w.code(6)
