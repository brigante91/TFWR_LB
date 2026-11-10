"""Verifica geometrica offline di lb_hay_dense2.py (o lb_hay_dense.py).
Esegue le funzioni r_i con un ambiente finto che registra move/plant/early, poi controlla:
 - ogni percorso parte da (0,0) e finisce sulla propria A;
 - early() e' chiamata esattamente su A (con other = C) e su C (con other = A), una volta ciascuna;
 - nessun cespuglio e' piantato su una delle 64 erbe; nessuna cella piantata due volte;
 - ogni erba ha 23 cespugli nel rombo di raggio 3 (tutte le celle tranne la compagna);
 - i dizionari restituiti contengono esattamente (BUSH, p) per le 23 celle del rombo;
 - DIRS: d2 porta da A a C, d1 da C ad A.
uso: python3 verify2.py ../lb_hay_dense2.py"""
import sys, re
S = 32
D = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) if (dx or dy) and abs(dx) + abs(dy) <= 3]
VEC = {"East": (1, 0), "West": (-1, 0), "North": (0, 1), "South": (0, -1)}

path = sys.argv[1] if len(sys.argv) > 1 else "../lb_hay_dense2.py"
src = open(path).read().replace("\t", "    ")
# estrai solo le definizioni r_i, ROUTES e DIRS/PARAMS
parts = re.findall(r"^def r\d+\(\):\n(?:    .*\n|\n)*", src, flags=re.M)
assert len(parts) == 32, len(parts)
m_routes = re.search(r"^ROUTES = .*$", src, flags=re.M).group(0)
m_dirs = re.search(r"^DIRS = \[\n(?:.*\n)*?\]", src, flags=re.M)
m_params = re.search(r"^PARAMS = \[\n(?:.*\n)*?\]", src, flags=re.M)

class Fake:
    def __init__(self):
        self.pos = (0, 0); self.plants = []; self.early = []
    def move(self, d):
        v = VEC[d]; self.pos = ((self.pos[0] + v[0]) % S, (self.pos[1] + v[1]) % S)
    def plant(self, what):
        assert what == "BUSH"; self.plants.append(self.pos)
    def early_(self, other):
        self.early.append((self.pos, tuple(other)))

env = {"East": "East", "West": "West", "North": "North", "South": "South", "BUSH": "BUSH"}
fake = Fake()
env["move"] = fake.move; env["plant"] = fake.plant; env["early"] = fake.early_
exec("\n".join(parts) + "\n" + m_routes, env)
routes = env["ROUTES"]
if m_dirs:
    exec(m_dirs.group(0), env); dirs = env["DIRS"]
else:
    exec(m_params.group(0), env); dirs = [(p[4], p[5]) for p in env["PARAMS"]]
    pairs_from_params = [((p[0], p[1]), (p[2], p[3])) for p in env["PARAMS"]]

errors = 0
def err(msg):
    global errors
    errors += 1; print("ERRORE:", msg)

all_plants = []
pairs = []
dicts = []
for i, r in enumerate(routes):
    fake.__init__()
    ret = r()
    if m_dirs:
        if not fake.early or len(fake.early) != 2:
            err("drone %d: early() chiamata %d volte" % (i, len(fake.early)))
            continue
        (p1, o1), (p2, o2) = fake.early
        if p1 != o2 or p2 != o1:
            err("drone %d: early() su %s (other %s) e %s (other %s) incoerenti" % (i, p1, o1, p2, o2))
        A = fake.pos
        C = o1 if p1 == A else p1
        if {p1, p2} != {A, C}:
            err("drone %d: visita anticipata su %s/%s ma A=%s" % (i, p1, p2, A))
        okA, okC = ret
        dicts.append((A, C, okA, okC))
    else:
        A, C = pairs_from_params[i]
        if fake.pos != A:
            err("drone %d: finisce su %s invece di A=%s" % (i, fake.pos, A))
    d1, d2 = dirs[i]
    v2 = VEC[d2]
    if ((A[0] + v2[0]) % S, (A[1] + v2[1]) % S) != C:
        err("drone %d: d2=%s non porta da A=%s a C=%s" % (i, d2, A, C))
    v1 = VEC[d1]
    if ((C[0] + v1[0]) % S, (C[1] + v1[1]) % S) != A:
        err("drone %d: d1=%s non porta da C a A" % (i, d1))
    pairs.append((A, C))
    all_plants += fake.plants
    print("drone %2d: %2d piantate, %2d mosse, fine su %s" % (i, len(fake.plants), len(fake.plants) and sum(1 for _ in []) or 0, fake.pos)) if False else None

grass = set(c for pr in pairs for c in pr)
if len(grass) != 64:
    err("erbe distinte: %d" % len(grass))
plants = set(all_plants)
if len(plants) != len(all_plants):
    from collections import Counter
    dup = [c for c, n in Counter(all_plants).items() if n > 1]
    err("celle piantate piu' volte: %s" % dup)
if plants & grass:
    err("cespugli sulle erbe: %s" % sorted(plants & grass))
need = set()
for A, C in pairs:
    for g, o in ((A, C), (C, A)):
        cells = set(((g[0] + dx) % S, (g[1] + dy) % S) for dx, dy in D)
        if o not in cells:
            err("coppia %s/%s non adiacente" % (A, C))
        cells.discard(o)
        if len(cells) != 23:
            err("erba %s: rombo con %d celle" % (g, len(cells)))
        missing = cells - plants
        if missing:
            err("erba %s: cespugli mancanti %s" % (g, sorted(missing)))
        extra_grass = cells & grass
        if extra_grass:
            err("erba %s: altre erbe nel rombo %s" % (g, sorted(extra_grass)))
        need |= cells
useless = plants - need
if useless:
    err("cespugli inutili: %s" % sorted(useless))
for A, C, okA, okC in dicts:
    for g, o, ok in ((A, C, okA), (C, A, okC)):
        cells = set(((g[0] + dx) % S, (g[1] + dy) % S) for dx, dy in D) - {o}
        keys = set(k[1] for k in ok)
        if any(k[0] != "BUSH" for k in ok) or keys != cells or len(ok) != 23:
            err("erba %s: dizionario con %d voci, differenze %s" % (g, len(ok), sorted(keys ^ cells)))
print("coppie %d, erbe %d, cespugli piantati %d, necessari %d, errori %d" % (len(pairs), len(grass), len(plants), len(need), errors))
sys.exit(1 if errors else 0)
