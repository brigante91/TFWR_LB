"""Esegue uno script di gioco (lb_sunflowers_v11.py) cosi' com'e' sopra il mondo di sim3.

Serve a controllare la LOGICA dello script vero (non una trascrizione): ogni drone e' un thread,
gira uno alla volta (quello col tick piu' basso) e cede il turno a ogni funzione del gioco.
Il codice fra due chiamate costa OPC tick fissi (stima), le azioni 200: i tempi sono vicini a
quelli di sim3/prog11 ma non identici; contano gli errori (semine fallite, raccolti a vuoto,
raccolti non massimi) e l'ordine di grandezza del tempo.
Uso: python3 harness.py script.py [seed] [opc]
"""
import os
import random
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim3

S = 32


class Killed(BaseException):
    pass


class D:
    def __init__(self, i, tick, seed):
        self.id = i
        self.tick = tick
        self.x = 0
        self.y = 0
        self.ev = threading.Event()
        self.alive = True
        self.killed = False
        self.rv = random.Random(seed * 1000003 + i * 7919 + 1)
        self.rr = random.Random(seed * 1000003 + i * 7919 + 2)


class Game:
    def __init__(self, path, seed=0, opc=5.0, goal=sim3.GOAL, jit=200.0, verbose=False):
        self.W = sim3.World(seed)
        self.seed = seed
        self.opc = opc
        self.goal = goal
        self.jit = jit
        self.verbose = verbose
        self.drones = []
        self.local = threading.local()
        self.wrng = random.Random(seed * 31 + 5)
        self.wait_off = {}
        self.end = None
        self.cnt = {}
        self.err = None
        self.src = open(path).read()
        self.done = threading.Event()

    # ---- scheduler ----
    def me(self):
        return self.local.d

    def stat(self, k, n=1):
        self.cnt[k] = self.cnt.get(k, 0) + n

    def turn(self, cost=None):
        d = self.me()
        if d.killed:
            raise Killed()
        d.tick += self.opc if cost is None else cost
        self.pass_baton(d)
        if d.killed:
            raise Killed()
        self.W.advance(d.tick)

    def pass_baton(self, d):
        nxt = None
        for o in self.drones:
            if o.alive and (nxt is None or (o.tick, o.id) < (nxt.tick, nxt.id)):
                nxt = o
        if nxt is not d and nxt is not None:
            d.ev.clear()
            nxt.ev.set()
            if d.alive:
                d.ev.wait()

    def start_drone(self, fn, tick):
        d = D(len(self.drones), tick, self.seed)
        par = self.me() if hasattr(self.local, 'd') else None
        if par is not None:
            d.x, d.y = par.x, par.y
        self.drones.append(d)
        self.W.active = sum(1 for o in self.drones if o.alive)

        def body():
            self.local.d = d
            d.ev.wait()
            try:
                if not d.killed:
                    self.W.advance(d.tick)
                    fn()
            except Killed:
                pass
            except BaseException as e:      # errore dello script
                import traceback
                self.err = traceback.format_exc()
                for o in self.drones:
                    o.killed = True
            d.alive = False
            self.W.active = sum(1 for o in self.drones if o.alive)
            if self.err is not None or not any(o.alive for o in self.drones):
                for o in self.drones:
                    o.ev.set()
                self.done.set()
                return
            self.pass_baton(d)

        th = threading.Thread(target=body, daemon=True)
        th.start()
        return d

    # ---- funzioni del gioco ----
    def cell(self, d):
        return d.y * S + d.x

    def g_move(self, direction):
        self.turn()
        d = self.me()
        dx, dy = direction
        d.x = (d.x + dx) % S
        d.y = (d.y + dy) % S
        d.tick += 200
        self.stat('move')
        return True

    def g_plant(self, ent):
        self.turn()
        d = self.me()
        W = self.W
        c = self.cell(d)
        if W.val[c] or W.grass[c] and not W.soil[c] or not W.soil[c]:
            d.tick += 1
            self.stat('plant_fail')
            return False
        v = d.rv.randint(7, 15)
        rf = 1.0 - sim3.DEV + 2 * sim3.DEV * d.rr.random()
        W.plant(c, W.time(d.tick), v, rf)
        d.tick += 200
        self.stat('plant')
        return True

    def g_harvest(self):
        self.turn()
        d = self.me()
        W = self.W
        c = self.cell(d)
        if W.val[c]:
            W.harvest(c, d.tick)
            d.tick += 200
            self.stat('harvest')
            return True
        if W.grass[c]:
            W.grass[c] = False
            d.tick += 200
            self.stat('harvest_grass')
            return True
        d.tick += 1
        self.stat('harvest_fail')
        return False

    def g_till(self):
        self.turn()
        d = self.me()
        W = self.W
        c = self.cell(d)
        if W.val[c]:
            W.cnt[W.val[c]] -= 1
            W.nsun -= 1
            W.val[c] = 0
            self.stat('till_on_sunflower')
        if W.soil[c]:
            W.soil[c] = False
            W.grass[c] = True
        else:
            W.soil[c] = True
            W.grass[c] = False
        d.tick += 200
        self.stat('till')

    def g_measure(self, direction=None):
        self.turn()
        d = self.me()
        d.tick += 1
        x, y = d.x, d.y
        if direction is not None:
            x = (x + direction[0]) % S
            y = (y + direction[1]) % S
        v = self.W.val[y * S + x]
        return v if v else None

    def g_can_harvest(self):
        self.turn()
        d = self.me()
        d.tick += 1
        c = self.cell(d)
        return bool(self.W.val[c]) and self.W.grown(c, self.W.time(d.tick))

    def g_get_entity_type(self):
        self.turn()
        d = self.me()
        d.tick += 1
        c = self.cell(d)
        if self.W.val[c]:
            return 'Sunflower'
        if self.W.grass[c]:
            return 'Grass'
        return None

    def g_get_ground_type(self):
        self.turn()
        d = self.me()
        d.tick += 1
        return 'Soil' if self.W.soil[self.cell(d)] else 'Grassland'

    def g_get_time(self):
        self.turn(1.0)
        return self.W.time(self.me().tick)

    def g_get_water(self):
        self.turn()
        d = self.me()
        d.tick += 1
        return self.W.water_now(self.cell(d), self.W.time(d.tick))

    def g_use_item(self, item, n=1):
        self.turn()
        d = self.me()
        W = self.W
        n = int(n)
        t = W.time(d.tick)
        if item != 'Water':
            raise RuntimeError('use_item non previsto: %r' % (item,))
        if n >= 1 and W.tank(t) >= n:
            W.tank_used += n
            W.add_water(self.cell(d), t, n)
            d.tick += 200
            self.stat('water')
            return True
        d.tick += 1
        self.stat('water_fail')
        return False

    def g_num_items(self, item):
        self.turn()
        d = self.me()
        d.tick += 1
        if item == 'Power':
            return self.W.power
        if item == 'Water':
            return self.W.tank(self.W.time(d.tick))
        return 0

    def g_spawn_drone(self, fn):
        self.turn()
        d = self.me()
        if sum(1 for o in self.drones if o.alive) >= 32:
            d.tick += 1
            return None
        nd = self.start_drone(fn, d.tick + 200)
        d.tick += 200
        return nd

    def g_clear(self):
        self.turn()
        d = self.me()
        for o in self.drones:
            if o is not d and o.alive:
                o.killed = True
                o.alive = False
        self.W.active = 1
        d.tick += 200
        self.W.advance(d.tick)
        if self.end is None:
            self.end = (self.W.time(d.tick), self.W.power >= self.goal)
        for o in self.drones:
            if o is not d:
                o.ev.set()

    def g_wait_until(self, tgt):
        # sostituisce 'while get_time() < t: pass' dello script (stesso modello di sim3)
        d = self.me()
        while True:
            self.turn(3.0)
            if self.W.time(d.tick) >= tgt:
                return
            key = round(tgt, 9)
            if key not in self.wait_off:
                self.wait_off[key] = self.wrng.random() * self.jit
            d.tick = max(d.tick, self.W.tick_of(tgt) + self.wait_off[key] - 3.0)

    def run(self, timeout=600.0):
        W = self.W
        W.soil = [False] * (S * S)
        g = {
            '__name__': 'game',
            'North': (0, 1), 'South': (0, -1), 'East': (1, 0), 'West': (-1, 0),
            'Entities': type('E', (), {'Sunflower': 'Sunflower', 'Grass': 'Grass'}),
            'Grounds': type('G', (), {'Soil': 'Soil', 'Grassland': 'Grassland'}),
            'Items': type('I', (), {'Water': 'Water', 'Power': 'Power'}),
            'move': self.g_move, 'plant': self.g_plant, 'harvest': self.g_harvest, 'till': self.g_till,
            'measure': self.g_measure, 'can_harvest': self.g_can_harvest,
            'get_entity_type': self.g_get_entity_type, 'get_ground_type': self.g_get_ground_type,
            'get_time': self.g_get_time, 'get_water': self.g_get_water, 'use_item': self.g_use_item,
            'num_items': self.g_num_items, 'spawn_drone': self.g_spawn_drone, 'clear': self.g_clear,
            'get_world_size': lambda: S,
            'get_pos_x': lambda: self.me().x, 'get_pos_y': lambda: self.me().y,
            'quick_print': (print if self.verbose else (lambda *a: None)),
        }
        code = compile(self.src, 'script', 'exec')

        def main():
            # le definizioni dello script, poi il corpo; wait_until nativo
            src_defs = self.src
            exec(code, g)

        # wait_until nativo: lo script lo definisce, quindi va sostituito dopo le def ma prima
        # dell'uso; si inietta una riga subito dopo la sua definizione
        marker = "def wait_until(t):\n\twhile get_time() < t:\n\t\tpass\n"
        if marker not in self.src:
            raise RuntimeError('wait_until non trovato nello script')
        src2 = self.src.replace(marker, marker + "wait_until = _native_wait\n")
        g['_native_wait'] = self.g_wait_until
        code = compile(src2, 'script', 'exec')
        d0 = self.start_drone(main, 0.0)
        d0.ev.set()
        self.done.wait(timeout)
        if self.err:
            raise RuntimeError(self.err)
        if self.end is None:
            t = max(o.tick for o in self.drones)
            self.end = (W.time(t), W.power >= self.goal)
        return dict(t=self.end[0], ok=self.end[1], power=W.power, boost=W.nboost, plain=W.nplain, zero=W.nzero,
                    lost=W.nlost, zmax=W.nzmax, notmax=W.nnotmax, tank=W.tank_used, cnt=dict(self.cnt))


if __name__ == '__main__':
    path = sys.argv[1]
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    opc = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
    r = Game(path, seed, opc, verbose=len(sys.argv) > 4).run()
    print(r)
