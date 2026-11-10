"""Simulatore a eventi della classifica Sunflowers (32 droni, 100.000 power), drone per drone.

Sostituisce il modello aggregato di sunsim.py per gli script a blocchi 4x8 (v5 e seguenti).
Ogni drone esegue una trascrizione dello script con i costi dell'interprete
(FINDINGS_cactus_dino_maze.md): azione 200 tick (1 se fallisce), measure/get_* /num_items 1,
operatore/confronto/indice/if 1, for 1 per giro, while 1 alla prima valutazione + costo della
condizione a ogni valutazione, chiamata a funzione propria 1, get_time e quick_print 0.

Regole del gioco (decompiled_full/Core):
  - Sunflower.Harvest: boost = (petali == max del campo, semi compresi) e >= 10 girasoli;
    flag globale = !boost; se il flag era gia' vero il raccolto perde il bonus. Resa 8/1 se
    cresciuto, 0 se seme (ma il flag si aggiorna lo stesso).
  - crescita 5 s * U[0.8,1.2] / (1 + 4 * acqua), con l'acqua che cambia durante la crescita
    (Growable.TryScheduleGrow conserva la percentuale cresciuta); acqua della CELLA, resta
    dopo il raccolto; decadimento 0.99 con prob. 0.1 ogni 0.1 s (qui la media continua).
  - serbatoio: +1 ogni 20/512 s da t=0; use_item(Water,n) fallisce (1 tick) se < n.
  - power: Farm.UsePower ogni 0.2 s toglie ops/6000 (tutti i droni); con power 0 la velocita'
    e' dimezzata (3037.5 tick/s), torna piena al primo raccolto con resa.
  - fine run: Execution si ferma quando restano zero programmi; clear() toglie tutti gli altri
    droni (qualunque drone lo chiami). Successo = power >= GOAL in quell'istante.
  - get_time durante un'attesa attiva: l'esecuzione procede a passi di ~200 tick, quindi
    wait_until esce in ritardo di U[0,200) tick (lo stesso per tutti i droni che aspettano).
Ordine degli effetti: per tick del drone, poi id (Execution.Execute).

Variabili casuali: ogni drone ha i suoi flussi (petali, randomFactor) dal seed, cosi' due
varianti dello script vedono le stesse sequenze (numeri casuali comuni).
"""
import heapq, math, random

TPS = 6075.0
S = 32
GOAL = 100000
TANK_DT = 20.0 / 512
LAM = -math.log(0.99) * 1.0          # decadimento medio acqua per secondo (1 evento/s)
USE_DT = 0.2
GROW = 7.0         # crescita media (s): 7 tarato sui test in gioco del 7 nov (5 non torna)
DEV = 0.2          # deviazione del randomFactor


class World:
    def __init__(self, seed, nd=32):
        self.seed = seed
        self.nd = nd
        n = S * S
        self.val = [0] * n          # 0 = niente girasole
        self.grass = [True] * n
        self.soil = [False] * n
        self.prog = [0.0] * n       # percentuale cresciuta alla data tlast
        self.rf = [1.0] * n
        self.w = [0.0] * n          # acqua alla data tw
        self.tw = [0.0] * n
        self.tl = [0.0] * n
        self.cnt = [0] * 17
        self.nsun = 0
        self.flag = False
        self.power = 0.0
        self.gross = 0.0
        self.tank_used = 0
        # orologio: segmento corrente
        self.seg_tick = 0.0
        self.seg_time = 0.0
        self.tps = TPS / 2
        self.next_use = USE_DT
        self.use_tick = 0.0         # tick globale dell'ultimo UsePower
        self.used = 0.0
        self.active = 1
        self.nboost = 0
        self.nplain = 0
        self.nzero = 0
        self.trace = []
        self.nzmax = 0
        self.nnotmax = 0
        self.nlost = 0               # raccolti di un massimo cresciuto che perdono il bonus

    # ---- tempo ----
    def time(self, tick):
        return self.seg_time + (tick - self.seg_tick) / self.tps

    def tick_of(self, t):
        return self.seg_tick + (t - self.seg_time) * self.tps

    def set_speed(self, tick, tps):
        if tps == self.tps:
            return
        self.seg_time = self.time(tick)
        self.seg_tick = tick
        self.tps = tps

    def advance(self, tick):
        # processa i UsePower fino al tick (tempo) corrente
        while self.time(tick) >= self.next_use:
            tu = self.tick_of(self.next_use)
            self.used += self.active * (tu - self.use_tick) / 6000.0
            self.use_tick = tu
            if self.power > 0:
                self.power -= self.used
                if self.power <= 0:
                    self.power = 0.0
                    self.set_speed(tu, TPS / 2)
            self.used = 0.0
            self.next_use += USE_DT

    def add_power(self, tick, amt):
        if amt <= 0:
            return
        if self.power == 0.0:
            self.used = 0.0
            self.use_tick = tick
            self.set_speed(tick, TPS)
        self.power += amt
        self.gross += amt

    # ---- acqua / crescita ----
    def water_now(self, c, t):
        return self.w[c] * math.exp(-LAM * (t - self.tw[c]))

    def _upd(self, c, t):
        # porta prog e acqua al tempo t
        if self.val[c]:
            dt = t - self.tl[c]
            if dt > 0 and self.prog[c] < 1.0:
                w0 = self.water_now(c, self.tl[c])
                integ = dt + 4.0 * w0 * (1 - math.exp(-LAM * dt)) / LAM
                self.prog[c] = min(1.0, self.prog[c] + integ / (GROW * self.rf[c]))
            self.tl[c] = t
        self.w[c] = self.water_now(c, t)
        self.tw[c] = t

    def grown(self, c, t):
        self._upd(c, t)
        return self.prog[c] >= 1.0 - 1e-12

    def add_water(self, c, t, n):
        self._upd(c, t)
        self.w[c] = min(1.0, self.w[c] + 0.25 * n)

    def tank(self, t):
        return int(t / TANK_DT) - self.tank_used

    # ---- azioni sul campo ----
    def plant(self, c, t, v, rf):
        self._upd(c, t)
        self.val[c] = v
        self.prog[c] = 0.0
        self.rf[c] = rf
        self.tl[c] = t
        self.cnt[v] += 1
        self.nsun += 1

    def harvest(self, c, tick):
        v = self.val[c]
        t = self.time(tick)
        g = self.grown(c, t)
        mx = 16
        while mx > 7 and self.cnt[mx] == 0:
            mx -= 1
        boost = (v == mx) and self.nsun >= 10
        if v == mx and not g:
            self.nzmax += 1
        if v != mx and g:
            self.nnotmax += 1
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
            if boost:
                self.nboost += 1
                self.add_power(tick, 8.0)
            else:
                self.nplain += 1
                self.add_power(tick, 1.0)
        else:
            self.nzero += 1


class Drone:
    __slots__ = ("id", "tick", "gen", "rv", "rr", "alive", "send", "req")

    def __init__(self, i, tick, gen, seed):
        self.id = i
        self.tick = tick
        self.gen = gen
        self.rv = random.Random(seed * 1000003 + i * 7919 + 1)   # petali
        self.rr = random.Random(seed * 1000003 + i * 7919 + 2)   # randomFactor
        self.alive = True
        self.send = None
        self.req = None


def simulate(prog, P, seed, maxtime=600.0, goal=GOAL):
    """prog(drone, P, main) e' un generatore che produce richieste (ops_codice, tipo, ...).
    Ritorna dict con tempo finale, successo e statistiche."""
    W = World(seed)
    wrng = random.Random(seed * 31 + 5)       # ritardo delle attese attive
    wait_off = {}
    heap = []
    drones = []
    seq = [0]

    def push(d):
        seq[0] += 1
        heapq.heappush(heap, (d.tick, d.id, seq[0], d))

    def spawn(tick):
        d = Drone(len(drones), tick, None, seed)
        drones.append(d)
        W.active = len(drones)
        return d

    d0 = spawn(0.0)
    d0.gen = prog(d0, P, True)
    push(d0)
    end = None
    while heap:
        tick, _, _, d = heapq.heappop(heap)
        if not d.alive:
            continue
        if d.req is None:
            try:
                req = d.gen.send(d.send)
            except StopIteration:
                d.alive = False
                continue
            d.send = None
            d.tick += req[0]
            d.req = req
            if req[1] == 'wait':
                W.advance(d.tick)
                tgt = req[2]
                if W.time(d.tick) < tgt:
                    key = round(tgt, 9)
                    if key not in wait_off:
                        wait_off[key] = wrng.random() * 200.0
                    d.tick = W.tick_of(tgt) + wait_off[key]
            if heap and heap[0][0] < d.tick:
                push(d)
                continue
        req = d.req
        k = req[1]
        W.advance(d.tick)
        t = W.time(d.tick)
        if t > maxtime:
            end = (t, False)
            break
        d.req = None
        if k == 'wait':
            tgt = req[2]
            if t < tgt:          # la velocita' e' cambiata durante l'attesa: ricalcola
                d.req = req
                d.tick = W.tick_of(tgt) + wait_off[round(tgt, 9)]
        elif k == 'plant':
            c = req[2]
            v = d.rv.randint(7, 15)
            rf = 1.0 - DEV + 2 * DEV * d.rr.random()
            W.plant(c, t, v, rf)
            W.grass[c] = False
            d.send = v
            d.tick += 200
        elif k == 'harv':
            c = req[2]
            if W.val[c]:
                W.harvest(c, d.tick)
                d.tick += 200
                d.send = True
            elif W.grass[c]:
                W.grass[c] = False
                d.tick += 200
                d.send = True
            else:
                d.tick += 1
                d.send = False
        elif k == 'water':
            c, n = req[2], req[3]
            if n >= 1 and W.tank(t) >= n:
                W.tank_used += n
                W.add_water(c, t, n)
                d.tick += 200
                d.send = True
            else:
                d.tick += 1
                d.send = False
        elif k == 'getw':
            d.send = W.water_now(req[2], t)
            d.tick += 1
        elif k == 'canh':
            c = req[2]
            d.send = bool(W.val[c]) and W.grown(c, t)
            d.tick += 1
        elif k == 'num':
            d.send = W.power
            d.tick += 1
        elif k == 'time':
            d.send = t
        elif k == 'trace':
            W.trace.append((round(t, 2), round(W.power, 1), req[2]))
        elif k == 'spawn':
            nd = spawn(d.tick + 200)
            nd.gen = req[2](nd)
            push(nd)
            d.tick += 200
        elif k == 'clear':
            for x in drones:
                if x is not d:
                    x.alive = False
            W.active = 1
            d.tick += 200
            W.advance(d.tick)
            end = (W.time(d.tick), W.power >= goal)
            break
        push(d)
    if end is None:
        end = (W.time(max(x.tick for x in drones)), W.power >= goal)
    return dict(t=end[0], ok=end[1], power=W.power, boost=W.nboost, plain=W.nplain,
                zero=W.nzero, lost=W.nlost, zmax=W.nzmax, notmax=W.nnotmax, tank=W.tank_used, W=W)
