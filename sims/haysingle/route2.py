"""Percorso di semina piu' corto per Hay_Single: ricerca in profondita' dei cammini che partono da
(0, 0), piantano tutti i 30 cespugli e finiscono su A o C, con limite sulle mosse; tra i piu' corti
sceglie quello con piu' raccolti gratuiti attesi. Le erbe A, C possono stare in qualunque posizione
(il drone parte sempre da (0, 0)). Scrive route.json come route.py."""
import json, sys, random
from route import S, D3, w
sys.setrecursionlimit(10000)


def diamond(g):
    return {w((g[0] + dx, g[1] + dy)) for dx, dy in D3}


def nb(c):
    return [w((c[0] + dx, c[1] + dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]


def ev_of(path, A, C, bush):
    planted = set(); seen = {path[0]}; ev = 0.0
    for c in path[1:]:
        if c in seen:
            continue
        seen.add(c)
        n = sum(1 for d in diamond(c) if d in planted)
        ev += n / 72
        if c in bush:
            planted.add(c)
    return ev


best = None
for A in [(0, 0), (7, 0), (0, 7), (7, 7), (6, 0), (0, 1)]:
    for C in [w((A[0] + 1, A[1])), w((A[0] - 1, A[1]))]:
        bush = (diamond(A) | diamond(C)) - {A, C}
        for LIM in range(30, 36):
            found = []
            start = (0, 0)

            def dfs(cur, path, todo, moves):
                if len(found) > 4000:
                    return
                if not todo:
                    if cur in (A, C):
                        found.append(list(path))
                        return
                if moves >= LIM:
                    return
                # limite inferiore: ogni cespuglio mancante costa almeno una mossa
                if moves + len(todo) + (0 if todo else 1) > LIM:
                    return
                opts = nb(cur)
                opts.sort(key=lambda n: (n not in todo, sum(1 for m in nb(n) if m in todo)))
                for n in opts:
                    newly = n in todo
                    if not newly and todo and sum(1 for m in nb(n) if m in todo) == 0 and n not in (A, C):
                        # passaggio su cella gia' vista senza cespugli vicini: lo consente solo se serve
                        pass
                    if newly:
                        todo.discard(n)
                    path.append(n)
                    dfs(n, path, todo, moves + 1)
                    path.pop()
                    if newly:
                        todo.add(n)

            dfs(start, [start], set(bush) - {start}, 0)
            if found:
                for p in found:
                    ev = ev_of(p, A, C, bush)
                    val = ev * 640 - (len(p) - 1) * 200
                    if best is None or val > best[0]:
                        best = (val, ev, len(p) - 1, p, A, C)
                print("A=%s C=%s: minimo %d mosse (%d cammini)" % (A, C, LIM, len(found)), flush=True)
                break
val, ev, moves, p, A, C = best
end = p[-1]
print("migliore: A=%s C=%s mosse %d, raccolti gratuiti attesi %.2f, fine su %s" % (A, C, moves, ev, end))
json.dump({"A": A, "C": C, "path": p, "end": end}, open("route2.json", "w"))
