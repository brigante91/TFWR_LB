"""Percorso di semina: limite di parita' e ricerca casuale piu' ampia (A ovunque, C a est o ovest).
Scrive route2.json se trova meglio di route.json."""
import json, random, time
from route import S, D3, w


def diamond(g):
    return {w((g[0] + dx, g[1] + dy)) for dx, dy in D3}


def dist(a, b):
    dx = abs(a[0] - b[0]) % S; dy = abs(a[1] - b[1]) % S
    return min(dx, S - dx) + min(dy, S - dy)


ALL = [(x, y) for x in range(S) for y in range(S)]
NB = {c: [w((c[0] + dx, c[1] + dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))] for c in ALL}
A0 = (0, 0); C0 = (1, 0)
bush0 = (diamond(A0) | diamond(C0)) - {A0, C0}
blk = sum(1 for c in bush0 if (c[0] + c[1]) % 2 == 0); wht = len(bush0) - blk
print("cespugli neri %d bianchi %d (A nero, C bianco)" % (blk, wht))


def ev_of(path, bush):
    planted = set(); seen = {path[0]}; ev = 0.0
    for c in path[1:]:
        if c in seen:
            continue
        seen.add(c)
        ev += sum(1 for d in diamond(c) if d in planted) / 72
        if c in bush:
            planted.add(c)
    return ev


rng = random.Random(7)
best = None
t0 = time.time()
cands = [(A, w((A[0] + s, A[1]))) for A in ALL for s in (1, -1)]
while time.time() - t0 < 150:
    A, C = rng.choice(cands)
    bush = (diamond(A) | diamond(C)) - {A, C}
    cur = (0, 0); path = [cur]; todo = set(bush) - {cur}
    noise = rng.random() * 2
    while todo:
        opts = [n for n in NB[cur] if n in todo]
        if opts:
            nxt = min(opts, key=lambda n: sum(1 for m in NB[n] if m in todo) + rng.random() * noise)
        else:
            tgt = min(todo, key=lambda t: (dist(cur, t), rng.random()))
            nxt = min(NB[cur], key=lambda n: (dist(n, tgt), rng.random()))
        path.append(nxt); todo.discard(nxt); cur = nxt
    end = min((A, C), key=lambda g: dist(cur, g))
    while cur != end:
        cur = min(NB[cur], key=lambda n: dist(n, end)); path.append(cur)
    moves = len(path) - 1
    ev = ev_of(path, bush)
    val = ev * 640 - moves * 200
    if best is None or val > best[0]:
        best = (val, ev, moves, path, A, C, end)
val, ev, moves, path, A, C, end = best
print("migliore: A=%s C=%s mosse %d, raccolti gratuiti attesi %.2f, valore %.0f tick" % (A, C, moves, ev, val))
old = json.load(open("route.json"))
print("route.json attuale: 35 mosse, 3.57 attesi, valore %.0f" % (3.57 * 640 - 35 * 200))
json.dump({"A": A, "C": C, "path": path, "end": end}, open("route2.json", "w"))
