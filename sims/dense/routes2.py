"""Percorsi 'monotoni': ogni drone va dall'origine alla sua erba A per la via piu' corta
che raccoglie piu' cespugli ancora da piantare; poi i cespugli rimasti con inserimento minimo."""
import json
from layout import S, dist, analyse

pairs = [tuple(map(tuple, p)) for p in json.load(open("pairs.json"))["pairs"]]
grass, union, bad = analyse(pairs)

def signed(a, b):
    d = (b - a) % S
    return d if d <= S // 2 else d - S

def best_monotone(start, end, todo):
    dx = signed(start[0], end[0]); dy = signed(start[1], end[1])
    sx = 1 if dx >= 0 else -1; sy = 1 if dy >= 0 else -1
    W, H = abs(dx), abs(dy)
    # dp[i][j] = max celle raccolte arrivando a (start+i*sx, start+j*sy)
    cell = lambda i, j: ((start[0] + i * sx) % S, (start[1] + j * sy) % S)
    dp = [[-1] * (H + 1) for _ in range(W + 1)]
    par = {}
    for i in range(W + 1):
        for j in range(H + 1):
            v = 1 if cell(i, j) in todo else 0
            if i == 0 and j == 0:
                dp[i][j] = 0; continue
            best = -1
            if i > 0 and dp[i - 1][j] > best: best = dp[i - 1][j]; par[(i, j)] = (i - 1, j)
            if j > 0 and dp[i][j - 1] > best: best = dp[i][j - 1]; par[(i, j)] = (i, j - 1)
            dp[i][j] = best + v
    path = []; ij = (W, H)
    while ij != (0, 0):
        path.append(cell(*ij)); ij = par[ij]
    path.reverse()
    return [c for c in path if c in todo]

order = sorted(range(32), key=lambda i: -min(dist((0, 0), g) for g in pairs[i]))
todo = set(union)
plan = []
for i in range(32):
    plan.append(None)
for i in order:
    pr = pairs[i]
    best = None
    for A in pr:
        got = best_monotone((0, 0), A, todo)
        if best is None or len(got) > len(best[1]):
            best = (A, got)
    A, got = best
    for c in got: todo.discard(c)
    C = pr[1] if A == pr[0] else pr[0]
    plan[i] = {"pair": pr, "A": A, "C": C, "path": [(0, 0)] + got + [A]}

def plen(path):
    return sum(dist(path[k], path[k + 1]) for k in range(len(path) - 1))

def two_opt(path):
    improved = True
    while improved:
        improved = False
        for i in range(1, len(path) - 2):
            for j in range(i + 1, len(path) - 1):
                a, b, c, d = path[i - 1], path[i], path[j], path[j + 1]
                if dist(a, c) + dist(b, d) < dist(a, b) + dist(c, d):
                    path[i:j + 1] = reversed(path[i:j + 1]); improved = True
    return path

# celle rimaste: inserimento a costo minimo in qualunque percorso
for c in sorted(todo, key=lambda c: -min(dist(c, g) for g in grass)):
    best = None
    for p in plan:
        path = p["path"]
        for k in range(len(path) - 1):
            add = dist(path[k], c) + dist(c, path[k + 1]) - dist(path[k], path[k + 1])
            if best is None or add < best[0]:
                best = (add, p, k + 1)
    best[1]["path"].insert(best[2], c)
for p in plan:
    two_opt(p["path"])
    p["moves"] = plen(p["path"]); p["plants"] = len(p["path"]) - 2
    p["A"] = list(p["A"]); p["C"] = list(p["C"]); p["path"] = [list(c) for c in p["path"]]
tot = sum(p["moves"] + p["plants"] for p in plan)
print("azioni medie per drone %.1f (prima 37.1); mosse %d piantate %d; min/max %d/%d" % (tot / 32, sum(p["moves"] for p in plan), sum(p["plants"] for p in plan), min(p["moves"] + p["plants"] for p in plan), max(p["moves"] + p["plants"] for p in plan)))
json.dump(plan, open("plan2.json", "w"))
