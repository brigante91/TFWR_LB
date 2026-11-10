"""Percorso di semina per Hay_Single: A = (0, 0) (il drone parte li'), C = (1, 0), cespugli su tutte
le altre celle dei due rombi di raggio 3 (toro 8x8). Cerca cicli hamiltoniani A -> ... -> A sulle 32
celle (1 mossa per passo) e tiene quello che massimizza i raccolti gratuiti attesi: su ogni cella
attraversata l'erba iniziale e' matura e il suo companion e' valido con prob. n/72, n = cespugli gia'
piantati nel suo rombo. Scrive route.json."""
import json, random
S = 8
A = (0, 0); C = (1, 0)
D3 = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) if (dx or dy) and abs(dx) + abs(dy) <= 3]


def w(p):
    return (p[0] % S, p[1] % S)


def diamond(g):
    return {w((g[0] + dx, g[1] + dy)) for dx, dy in D3}


union = diamond(A) | diamond(C) | {A, C}
bush = union - {A, C}
assert len(union) == 32 and len(bush) == 30
NB = {c: [w((c[0] + dx, c[1] + dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))] for c in union}
NB = {c: [n for n in v if n in union] for c, v in NB.items()}


def score_walk(path):
    # cespugli piantati alla prima visita; controllo gratuito alla prima visita di ogni cella non erba
    planted = set(); seen = {A}; ev = 0.0
    for c in path[1:]:
        if c in seen:
            continue
        seen.add(c)
        n = sum(1 for d in diamond(c) if d in planted and d not in (A, C))
        ev += n / 72
        if c in bush:
            planted.add(c)
    return ev


def score(path):
    planted = set(); ev = 0.0
    for c in path[1:-1]:
        if c == C:
            n = sum(1 for d in diamond(C) if d in planted and d != A)
            ev += n / 72
            continue
        n = sum(1 for d in diamond(c) if d in planted)
        ev += n / 72
        planted.add(c)
    return ev


def dist(a, b):
    dx = abs(a[0] - b[0]) % S; dy = abs(a[1] - b[1]) % S
    return min(dx, S - dx) + min(dy, S - dy)


ALL = {w((x, y)) for x in range(S) for y in range(S)}
NBALL = {c: [w((c[0] + dx, c[1] + dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))] for c in ALL}
best = None
rng = random.Random(1)
for attempt in range(60000):
    # cammino da A che pianta tutti i 30 cespugli; puo' ripassare su celle gia' viste (costo mossa)
    path = [A]; todo = set(bush); cur = A
    while todo:
        opts = [n for n in NBALL[cur] if n in todo]
        if opts:
            opts.sort(key=lambda n: (sum(1 for m in NBALL[n] if m in todo) + rng.random() * 1.5))
            nxt = opts[0]
        else:
            # vai verso la cella da piantare piu' vicina (passo per passo)
            tgt = min(todo, key=lambda t: (dist(cur, t), rng.random()))
            nxt = min(NBALL[cur], key=lambda n: (dist(n, tgt), rng.random()))
        path.append(nxt); todo.discard(nxt); cur = nxt
    # fine su A o su C, la cella piu' vicina
    end = min((A, C), key=lambda g: dist(cur, g))
    while cur != end:
        cur = min(NBALL[cur], key=lambda n: dist(n, end)); path.append(cur)
    moves = len(path) - 1
    sc = score_walk(path)
    val = sc * 640 - moves * 200
    if best is None or val > best[0]:
        best = (val, sc, moves, path, end)
val, sc, moves, path, end = best
print("mosse %d, raccolti gratuiti attesi %.2f, fine su %s" % (moves, sc, "A" if end == A else "C"))
json.dump({"A": A, "C": C, "path": path, "end": end}, open("route.json", "w"))
