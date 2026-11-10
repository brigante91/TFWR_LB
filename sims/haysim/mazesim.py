"""Simulatore della classifica Maze (9 863 168 oro, 32 droni, campo 32x32).

Esegue DIRETTAMENTE uno script nel dialetto del gioco (es. ../lb_maze_v2.py): ogni drone
e' un thread Python, i builtin (move, can_move, measure, use_item, harvest, plant,
spawn_drone, ...) sono forniti dal simulatore e costano i tick letti dall'IL
(azioni 200, fallite 1, sensori 1, get_time 0). Il costo della logica dell'interprete
e' stimato contando gli opcode Python eseguiti nei frame dello script (sys.settrace
con f_trace_opcodes) e convertendoli in tick con OPCODE_TICK (~0.4 tick per opcode:
tarato a mano sul ciclo principale, vedi calibrate()).

Regole del mondo (BushPlant.GenerateHedgeMaze, HedgePlant, Treasure, Drone.CanMove):
- use_item(WS, n) su un cespuglio genera un labirinto perfetto (DFS con direzioni in
  ordine casuale) di lato n/32; il quadrato cresce attorno al cespuglio alternando
  giu'-sinistra / su-destra (grow()); il tesoro e' in un vicolo cieco.
- measure() su siepe = posizione del tesoro (durante il trasloco: quella vecchia).
- use_item(WS, >= lato*32) sul tesoro: +lato^2*32 oro subito, trasloco di 200 tick in una
  cella casuale (nextPos scelta in anticipo), fallisce (200 tick) se gia' in trasloco,
  fallisce (1 tick) dopo 300 riusi (treasureFactor >= 301). A ogni trasloco ogni
  adiacenza interna si apre con p = 0.002.
- harvest() del tesoro: +lato^2*32 e rimozione di tutto il labirinto; harvest() di una
  siepe rimuove anch'esso il labirinto (senza oro).
- I timer scadono PRIMA delle operazioni dei droni allo stesso tick.
- Il drone 0 parte da (0,0) (clear()); spawn_drone: 200 tick al padre, il figlio nasce
  nella stessa cella e parte 200 tick dopo.

Uso:
  python3 mazesim.py [--script ../lb_maze_v2.py] [--set NOME=VALORE ...] [--runs N]
                     [--seed S] [--no-trace] [--quiet]
"""
import sys, os, re, heapq, random, threading, argparse, time

TPS = 6075.0
ACT = 200
GOAL = 9863168
S = 32
OPCODE_TICK = 0.4          # tick per opcode Python nei frame dello script (vedi calibrate)
NOTRACE_LOGIC = 3          # tick di logica aggiunti a ogni builtin quando il tracing e' spento
DIRV = [(0, 1), (1, 0), (0, -1), (-1, 0)]   # North, East, South, West (GridDirection)
REV = [2, 3, 0, 1]


class Stop(Exception):
    pass


class Direction:
    __slots__ = ("i", "name")

    def __init__(self, i, name):
        self.i = i
        self.name = name

    def __repr__(self):
        return self.name

    def __hash__(self):
        return self.i

    def __eq__(self, o):
        return isinstance(o, Direction) and o.i == self.i


class Sym:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class NS:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def grow(bx, by, desired, W=S):
    """Porta di BushPlant.GenerateHedgeMaze (parte di crescita del quadrato)."""
    num = 1
    ll = [bx, by]
    d = [-1, -1]
    failed = [False] * 4
    inb = lambda p: 0 <= p[0] < W and 0 <= p[1] < W
    while num < desired:
        p3 = ll[:]
        p4 = ll[:]
        if d[0] > 0:
            p3[1] += num if d[1] > 0 else -1
            p4[0] += num
            if d[1] < 0:
                p4[1] += num - 1
        else:
            p3[0] += num - 1
            p3[1] += num if d[1] > 0 else -1
            p4[0] -= 1
            if d[1] < 0:
                p4[1] += num - 1
        if inb(p3) and inb(p4):
            num += 1
            if d[0] < 0:
                ll[0] -= 1
            if d[1] < 0:
                ll[1] -= 1
            d = [-d[0], -d[1]]
            continue
        failed[(1 if d[0] > 0 else 0) + (2 if d[1] > 0 else 0)] = True
        k = 0
        while k < 3:
            d = [-d[1], d[0]]
            if failed[(1 if d[0] > 0 else 0) + (2 if d[1] > 0 else 0)]:
                k += 1
                continue
            break
        else:
            break
    return num, (ll[0], ll[1])


class Maze:
    def __init__(self, world, ll, n):
        self.world = world
        self.ll = ll
        self.n = n
        self.walls = {}          # (x,y) -> [N,E,S,W] True = muro
        self.treasure = None
        self.factor = 1
        self.repositioning = False
        self.next_pos = None
        self.removed = False
        self.reuses = 0
        self.t_gen = world.now()
        self.t_done = None
        self.use_times = []
        self.snap = None
        self.generate()
        if world.debug:
            self.snap = ({d.idx: d.pos for d in world.drones}, world.now(), {d.idx: d.moves for d in world.drones})

    def cells(self):
        x0, y0 = self.ll
        for i in range(self.n):
            for j in range(self.n):
                yield (x0 + i, y0 + j)

    def contains(self, p):
        return self.ll[0] <= p[0] < self.ll[0] + self.n and self.ll[1] <= p[1] < self.ll[1] + self.n

    def generate(self):
        rng = self.world.rng
        n = self.n
        arr = [None] * (n * n)
        start = rng.randrange(n * n)
        arr[start] = [True] * 4
        stack = [start]
        flag = False
        dead = []
        while stack:
            cur = stack[-1]
            cx, cy = cur % n, cur // n
            order = list(range(4))
            rng.shuffle(order)
            for d in order:
                nx, ny = cx + DIRV[d][0], cy + DIRV[d][1]
                if 0 <= nx < n and 0 <= ny < n and arr[nx + n * ny] is None:
                    nid = nx + n * ny
                    stack.append(nid)
                    arr[nid] = [True] * 4
                    arr[nid][REV[d]] = False
                    arr[cur][d] = False
                    flag = False
                    break
            if stack[-1] == cur:
                stack.pop()
                if not flag:
                    dead.append(cur)
                    flag = True
        tid = dead[rng.randrange(len(dead) - 1)]   # Next(Count-1): ultimo vicolo escluso
        x0, y0 = self.ll
        for i in range(n):
            for j in range(n):
                p = (x0 + i, y0 + j)
                self.walls[p] = arr[i + n * j]
                self.world.ent[p] = self
        self.treasure = (x0 + tid % n, y0 + tid // n)
        self.choose_next()

    def choose_next(self):
        rng = self.world.rng
        while True:
            p = (self.ll[0] + rng.randrange(self.n), self.ll[1] + rng.randrange(self.n))
            if p != self.treasure:
                self.next_pos = p
                return

    def reposition(self):
        """RepositionTreasure: ritorna (ok, costo_tick)."""
        if self.factor >= 301:
            return False, 1
        if self.repositioning:
            return False, ACT
        self.repositioning = True
        self.use_times.append(self.world.now())
        if self.world.debug and self.snap is not None:
            d = threading.current_thread().drone
            dist = self.bfs(self.treasure)
            orc = [(dist.get(p, 999), i) for i, p in self.snap[0].items()]
            orc.sort()
            own = dist.get(self.snap[0].get(d.idx), 999)
            self.world.rounds.append((self.world.now() - self.snap[1], d.idx, d.moves - self.snap[2].get(d.idx, 0),
                                      own, orc[0][0], orc[0][1], orc[1][0]))
        self.world.gold += self.n * self.n * 32
        self.world.add_timer(self.world.now() + ACT, self.complete)
        return True, ACT

    def complete(self):
        if not self.repositioning or self.removed:
            return
        self.repositioning = False
        self.treasure = self.next_pos
        self.factor += 1
        self.reuses += 1
        self.choose_next()
        rng = self.world.rng
        x0, y0 = self.ll
        n = self.n
        opened = 0
        for i in range(x0, x0 + n):
            for j in range(y0, y0 + n):
                if (i + j) % 2 == 1:
                    continue
                for d in range(4):
                    r = rng.random()
                    if r <= 0.002:
                        q = (i + DIRV[d][0], j + DIRV[d][1])
                        if x0 <= q[0] < x0 + n and y0 <= q[1] < y0 + n:
                            if self.walls[(i, j)][d]:
                                opened += 1
                            self.walls[(i, j)][d] = False
                            self.walls[q][REV[d]] = False
        self.world.opened += opened
        if self.world.debug:
            self.snap = ({d.idx: d.pos for d in self.world.drones}, self.world.now(),
                         {d.idx: d.moves for d in self.world.drones})

    def bfs(self, src):
        dist = {src: 0}
        q = [src]
        i = 0
        while i < len(q):
            c = q[i]
            i += 1
            for d in range(4):
                if not self.walls[c][d]:
                    m = (c[0] + DIRV[d][0], c[1] + DIRV[d][1])
                    if self.contains(m) and m not in dist:
                        dist[m] = dist[c] + 1
                        q.append(m)
        return dist

    def harvest_treasure(self):
        self.world.gold += self.n * self.n * 32
        self.remove()

    def remove(self):
        if self.removed:
            return
        self.removed = True
        self.t_done = self.world.now()
        for p in self.cells():
            if self.world.ent.get(p) is self:
                del self.world.ent[p]


class World:
    """Mondo + scheduler "a testimone": gira un solo thread-drone alla volta; a ogni
    operazione sincronizzata il drone si mette nello heap (clock, idx) e passa il
    testimone al drone con il clock minimo (= GlobalOpCount del gioco). I timer
    scadono prima dell'operazione del drone allo stesso tick."""

    def __init__(self, seed, trace=True, quiet=False, deadline=400.0):
        self.rng = random.Random(seed)
        self.ent = {}            # (x,y) -> Maze | 'bush'
        self.mazes = []
        self.gold = 0
        self.opened = 0
        self.timers = []
        self.tseq = 0
        self.drones = []
        self.heap = []
        self.stopped = False
        self.t_end = None
        self.trace = trace
        self.quiet = quiet
        self.deadline = deadline * TPS
        self.log = []
        self.debug = False
        self.rounds = []     # (tick del round, catcher, mosse del catcher, dist oracolo catcher, dist min, drone min, 2a dist)
        self.stats = {"moves": 0, "failed_moves": 0, "can_move": 0, "measure": 0,
                      "use_ok": 0, "use_fail": 0, "logic": 0.0}
        self.threads = []

    def now(self):
        return threading.current_thread().drone.clock

    def add_timer(self, t, fn):
        self.tseq += 1
        heapq.heappush(self.timers, (t, self.tseq, fn))

    def fire_timers(self, upto):
        while self.timers and self.timers[0][0] <= upto:
            t, _, fn = heapq.heappop(self.timers)
            fn()

    def next_event(self, drone):
        """Prossimo evento che puo' cambiare cio' che il drone osserva: un'azione di un
        drone nello stesso labirinto (o fuori da ogni labirinto) o un timer."""
        mz = self.ent.get(drone.pos)
        nxt = None
        for t, i in self.heap:
            d = self.drones[i]
            if d.idle:
                continue       # un drone in attesa attiva non cambia il mondo finche' qualcun altro non lo fa
            if mz is None or not isinstance(mz, Maze) or mz.contains(d.pos) or not isinstance(self.ent.get(d.pos), Maze):
                if nxt is None or t < nxt:
                    nxt = t
        if nxt is None and not self.timers:
            for t, i in self.heap:
                if nxt is None or t < nxt:
                    nxt = t
        if self.timers:
            t0 = self.timers[0][0]
            nxt = t0 if nxt is None else min(nxt, t0)
        return nxt

    def sync(self, drone):
        """Il drone deve eseguire un'operazione con effetto: aspetta il suo turno."""
        drone.flush_logic()
        if self.stopped:
            raise Stop()
        if drone.clock > self.deadline:
            self.finish()
            raise Stop()
        if self.heap and self.heap[0][0] < drone.clock:
            heapq.heappush(self.heap, (drone.clock, drone.idx))
            self.pass_baton()
            drone.ev.wait()
            drone.ev.clear()
            if self.stopped:
                raise Stop()
        self.fire_timers(drone.clock)

    def pass_baton(self):
        if self.heap:
            t, i = heapq.heappop(self.heap)
            self.drones[i].ev.set()

    def release(self, drone):
        """Il drone ha finito (o si e' fermato): passa il testimone."""
        drone.active = False
        drone.flush_logic()
        self.pass_baton()

    def finish(self):
        self.stopped = True
        self.t_end = max(d.clock for d in self.drones)


class Drone:
    def __init__(self, world, idx, pos, clock):
        self.world = world
        self.idx = idx
        self.pos = pos
        self.clock = clock
        self.active = True
        self.opcodes = 0
        self.thread = None
        self.last_key = None
        self.last_res = None
        self.last_clock = 0.0
        self.ev = threading.Event()
        self.moves = 0
        self.idle = False
        self.time_poll = -1e9

    def flush_logic(self):
        if self.opcodes:
            t = self.opcodes * OPCODE_TICK
            self.clock += t
            self.world.stats["logic"] += t
            self.opcodes = 0


def make_builtins(world, script_path):
    """Costruisce lo spazio dei nomi del gioco legato a `world`."""
    Items = NS(Weird_Substance=Sym("Weird_Substance"), Gold=Sym("Gold"), Power=Sym("Power"),
               Hay=Sym("Hay"))
    Entities = NS(Bush=Sym("Bush"), Hedge=Sym("Hedge"), Treasure=Sym("Treasure"), Grass=Sym("Grass"))
    Unlocks = NS(Mazes=Sym("Mazes"))
    DIRS = [Direction(i, n) for i, n in enumerate(["North", "East", "South", "West"])]

    def me():
        return threading.current_thread().drone

    def op(cost):
        """Operazione da 1 tick che legge il mondo: nessuna sincronizzazione stretta."""
        d = me()
        if world.stopped:
            raise Stop()
        d.last_key = None
        d.idle = False
        d.clock += cost + (0 if world.trace else NOTRACE_LOGIC)

    def idle_skip(d, key, res):
        """Attesa attiva (stesso sensore, stesso risultato, nessun'altra op in mezzo):
        salta al prossimo evento del mondo, dato che il risultato non puo' cambiare prima."""
        d.idle = False
        if d.last_key == key and d.last_res == res and d.clock - d.last_clock < 30:
            d.idle = True
            nxt = world.next_event(d)
            if d.clock - d.time_poll < 30:
                # il ciclo guarda anche l'orologio (scadenza ignota): avanza a piccoli passi
                lim = d.clock + 20
                if nxt is None or nxt > lim:
                    nxt = lim
            if nxt is not None and nxt > d.clock:
                d.clock = nxt
        d.last_key = key
        d.last_res = res
        d.last_clock = d.clock

    def action(fn):
        """Azione con effetto sul mondo: sincronizzata."""
        d = me()
        world.sync(d)
        d.last_key = None
        d.idle = False
        res, cost = fn(d)
        d.clock += cost + (0 if world.trace else NOTRACE_LOGIC)
        return res

    def wrap(p):
        return (p[0] % S, p[1] % S)

    def can_move_at(pos, di):
        q = wrap((pos[0] + DIRV[di][0], pos[1] + DIRV[di][1]))
        e1 = world.ent.get(q)
        e2 = world.ent.get(pos)
        if isinstance(e1, Maze) and e1.walls[q][REV[di]]:
            return False
        if isinstance(e2, Maze) and e2.walls[pos][di]:
            return False
        return True

    def move(dr):
        def f(d):
            if can_move_at(d.pos, dr.i):
                d.pos = wrap((d.pos[0] + DIRV[dr.i][0], d.pos[1] + DIRV[dr.i][1]))
                world.stats["moves"] += 1
                d.moves += 1
                return True, ACT
            world.stats["failed_moves"] += 1
            return False, 1
        return action(f)

    def can_move(dr):
        world.stats["can_move"] += 1
        op(1)
        return can_move_at(me().pos, dr.i)

    def measure(dr=None):
        world.stats["measure"] += 1
        d = me()
        world.sync(d)   # il valore dipende dai timer di trasloco
        pos = d.pos if dr is None else wrap((d.pos[0] + DIRV[dr.i][0], d.pos[1] + DIRV[dr.i][1]))
        e = world.ent.get(pos)
        res = None
        if isinstance(e, Maze):
            res = e.treasure
        idle_skip(d, "measure", res)
        d.clock += 1 + (0 if world.trace else NOTRACE_LOGIC)
        return res

    def can_harvest():
        d = me()
        world.sync(d)
        e = world.ent.get(d.pos)
        res = False
        if isinstance(e, Maze):
            res = not (e.treasure == d.pos and e.repositioning)
        d.clock += 1 + (0 if world.trace else NOTRACE_LOGIC)
        return res

    def get_entity_type():
        d = me()
        world.sync(d)
        d.last_key = None
        d.clock += 1 + (0 if world.trace else NOTRACE_LOGIC)
        e = world.ent.get(d.pos)
        if isinstance(e, Maze):
            return Entities.Treasure if e.treasure == d.pos else Entities.Hedge
        if e == "bush":
            return Entities.Bush
        return None

    def use_item(item, n=1):
        def f(d):
            e = world.ent.get(d.pos)
            if item is not Items.Weird_Substance:
                return False, 1
            if e == "bush":
                size = n // 32
                if size < 1:
                    return False, 1
                num, ll = grow(d.pos[0], d.pos[1], size)
                # SetEntity distrugge le siepi di altri labirinti sovrapposti
                for m in list(world.mazes):
                    if not m.removed and any(m.contains((ll[0] + i, ll[1] + j))
                                             for i in range(num) for j in range(num)):
                        m.remove()
                del world.ent[d.pos]
                mz = Maze(world, ll, num)
                world.mazes.append(mz)
                if ll[0] % num or ll[1] % num:
                    print("ATTENZIONE: labirinto %dx%d con origine %s (cespuglio %s)" % (num, num, ll, d.pos))
                return True, ACT
            if isinstance(e, Maze) and e.treasure == d.pos:
                if n // 32 < e.n:
                    return False, 1
                ok, cost = e.reposition()
                world.stats["use_ok" if ok else "use_fail"] += 1
                return ok, cost
            return False, 1
        return action(f)

    def harvest():
        def f(d):
            e = world.ent.get(d.pos)
            if isinstance(e, Maze):
                if e.treasure == d.pos:
                    if e.repositioning:
                        return False, ACT
                    e.harvest_treasure()
                    return True, ACT
                e.remove()
                return True, ACT
            if e == "bush":
                del world.ent[d.pos]
                return True, ACT
            return False, 1
        return action(f)

    def plant(ent):
        def f(d):
            if ent is not Entities.Bush or d.pos in world.ent:
                return False, 1
            world.ent[d.pos] = "bush"
            return True, ACT
        return action(f)

    def spawn_drone(fn, *args):
        def f(d):
            if len(world.drones) >= 32:
                return None, 1
            nd = Drone(world, len(world.drones), d.pos, d.clock + ACT)
            world.drones.append(nd)
            heapq.heappush(world.heap, (nd.clock, nd.idx))
            start_thread(nd, lambda: fn(*args))
            return nd, ACT
        return action(f)

    def get_pos_x():
        op(1)
        return me().pos[0]

    def get_pos_y():
        op(1)
        return me().pos[1]

    def get_time():
        d = me()
        d.time_poll = d.clock
        if world.stopped:
            raise Stop()
        d.flush_logic()
        if not world.trace:
            d.clock += NOTRACE_LOGIC
        return d.clock / TPS

    def get_tick_count():
        d = me()
        d.flush_logic()
        return d.clock

    def num_items(item):
        d = me()
        if item is Items.Gold:
            world.sync(d)
            res = world.gold
            idle_skip(d, "gold", res)
            d.clock += 1 + (0 if world.trace else NOTRACE_LOGIC)
            return res
        op(1)
        return 10 ** 9

    def num_unlocked(u):
        op(1)
        return 6

    def max_drones():
        op(1)
        return 32

    def get_world_size():
        op(1)
        return S

    def quick_print(*a):
        d = me()
        msg = "[d%02d %8.3fs] %s" % (d.idx, d.clock / TPS, " ".join(str(x) for x in a))
        world.log.append(msg)
        if not world.quiet:
            print(msg)

    def clear():
        d = me()
        world.sync(d)
        if world.mazes:        # chiusura finale
            world.finish()
            raise Stop()
        d.pos = (0, 0)
        d.clock += ACT

    def start_thread(drone, target):
        def run():
            threading.current_thread().drone = drone
            drone.ev.wait()          # aspetta il testimone
            drone.ev.clear()
            if world.trace:
                sys.settrace(tracer)
            try:
                if not world.stopped:
                    world.fire_timers(drone.clock)
                    target()
            except Stop:
                pass
            except Exception as ex:
                import traceback
                traceback.print_exc()
                world.finish()
            finally:
                sys.settrace(None)
                world.release(drone)
        th = threading.Thread(target=run, daemon=True)
        drone.thread = th
        world.threads.append(th)
        th.start()

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != script_path:
            return None
        frame.f_trace_opcodes = True
        d = threading.current_thread().drone
        if event == "opcode":
            d.opcodes += 1
        return tracer

    ns = dict(
        Items=Items, Entities=Entities, Unlocks=Unlocks,
        North=DIRS[0], East=DIRS[1], South=DIRS[2], West=DIRS[3],
        move=move, can_move=can_move, measure=measure, can_harvest=can_harvest,
        get_entity_type=get_entity_type, use_item=use_item, harvest=harvest, plant=plant,
        spawn_drone=spawn_drone, get_pos_x=get_pos_x, get_pos_y=get_pos_y,
        get_time=get_time, get_tick_count=get_tick_count, num_items=num_items,
        num_unlocked=num_unlocked, max_drones=max_drones, get_world_size=get_world_size,
        quick_print=quick_print, clear=clear,
    )
    return ns, start_thread


def run(script_path, overrides=None, seed=0, trace=True, quiet=True, deadline_s=400.0, debug=False):
    src = open(script_path).read()
    for k, v in (overrides or {}).items():
        src, n = re.subn(r"(?m)^%s = .*$" % re.escape(k), "%s = %s" % (k, v), src)
        if n == 0:
            raise SystemExit("costante %s non trovata nello script" % k)
    code = compile(src, script_path, "exec")
    world = World(seed, trace=trace, quiet=quiet, deadline=deadline_s)
    world.debug = debug
    world.dump = False
    ns, start_thread = make_builtins(world, script_path)
    main = Drone(world, 0, (0, 0), 0.0)
    world.drones.append(main)
    t0 = time.time()
    start_thread(main, lambda: exec(code, ns))
    main.ev.set()
    while True:
        alive = [th for th in world.threads if th.is_alive()]
        if not alive:
            break
        for th in alive:
            th.join(0.5)
        if not quiet and time.time() - t0 > getattr(world, "_next_prog", 10):
            world._next_prog = time.time() - t0 + 10
            mn = min((d.clock for d in world.drones if d.active), default=0)
            print("  ... sim %.1fs oro %d (wall %.0fs)" % (mn / TPS, world.gold, time.time() - t0), flush=True)
    if world.t_end is None:
        world.t_end = max(d.clock for d in world.drones)
    world.wall = time.time() - t0
    return world


def report(world):
    st = world.stats
    print("tempo simulato %.3f s (%d tick), oro %d, wall %.1fs" % (
        world.t_end / TPS, world.t_end, world.gold, world.wall))
    print("  mosse %d (fallite %d), can_move %d, measure %d, use ok %d / fail %d, logica %.0f tick (%.1f%%)" % (
        st["moves"], st["failed_moves"], st["can_move"], st["measure"], st["use_ok"], st["use_fail"],
        st["logic"], 100 * st["logic"] / max(1, sum(d.clock for d in world.drones))))
    if not world.quiet:
        for m in world.mazes:
            ds = [d for d in world.drones if m.contains(d.pos)]
            print("    labirinto %s: fine %7.2f s, riusi %d, droni %s" % (
                m.ll, (m.t_done or 0) / TPS, m.reuses, " ".join("d%d(%d mosse)" % (d.idx, d.moves) for d in ds)))
    # durata media dei round per finestre di 50 riusi (solo vite complete)
    win = {}
    for m in world.mazes:
        ts = [m.t_gen] + m.use_times
        for i in range(1, len(ts)):
            win.setdefault((i - 1) // 50, []).append(ts[i] - ts[i - 1])
    print("  tick/round per finestra di 50 riusi: " + " ".join(
        "%d-%d:%.0f" % (k * 50, k * 50 + 49, sum(v) / len(v)) for k, v in sorted(win.items())))
    if world.rounds:
        R = world.rounds
        n = len(R)
        def win(lo, hi):
            w = R[lo:hi]
            if not w:
                return ""
            k = len(w)
            return "%3d-%3d: tick %5.0f  mosse %5.1f  orc.catcher %4.1f  orc.min %4.1f  2a %4.1f  catcher=min %3.0f%%" % (
                lo, hi - 1, sum(x[0] for x in w) / k, sum(x[2] for x in w) / k, sum(x[3] for x in w) / k,
                sum(x[4] for x in w) / k, sum(x[6] for x in w) / k, 100.0 * sum(1 for x in w if x[1] == x[5]) / k)
        for lo in range(0, n, 50):
            print("  " + win(lo, lo + 50))
        if world.dump:
            for i, x in enumerate(R):
                print("   r%3d tick %5.0f catcher d%02d mosse %3d orc %3d | min %3d (d%02d) 2a %3d" % (
                    i, x[0], x[1], x[2], x[3], x[4], x[5], x[6]))
    done = [m for m in world.mazes if m.t_done]
    if done:
        print("  labirinti %d, generati %.2f-%.2f s, finiti %.2f-%.2f s, mosse/riuso %.2f, muri aperti %d" % (
            len(world.mazes), min(m.t_gen for m in world.mazes) / TPS, max(m.t_gen for m in world.mazes) / TPS,
            min(m.t_done for m in done) / TPS, max(m.t_done for m in done) / TPS,
            st["moves"] / max(1, sum(m.reuses + 1 for m in world.mazes)), world.opened))


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--script", default=os.path.join(here, "..", "lb_maze_v2.py"))
    ap.add_argument("--set", action="append", default=[], help="NOME=VALORE (sostituisce la costante)")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--no-trace", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--opcode-tick", type=float, default=OPCODE_TICK)
    ap.add_argument("--debug", action="store_true", help="statistiche per round (oracolo BFS)")
    ap.add_argument("--dump", action="store_true", help="stampa ogni round")
    a = ap.parse_args()
    globals()["OPCODE_TICK"] = a.opcode_tick
    ov = dict(s.split("=", 1) for s in a.set)
    times = []
    for r in range(a.runs):
        w = run(os.path.abspath(a.script), ov, seed=a.seed + r, trace=not a.no_trace, quiet=a.quiet or a.runs > 1,
                debug=a.debug or a.dump)
        w.dump = a.dump
        report(w)
        times.append(w.t_end / TPS)
    if a.runs > 1:
        times.sort()
        print("media %.3f s  min %.3f  max %.3f  (%d run)" % (sum(times) / len(times), times[0], times[-1], len(times)))


if __name__ == "__main__":
    main()
