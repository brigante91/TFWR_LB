"""Enumera giri chiusi di 8 alberi (passi di distanza 2, al massimo un passo di 4) e tutti i
reticoli di periodo 32 (indice 32); stima il costo per raccolto."""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from woodlay import analyze, wrap, S

STEPS2 = [(2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (1, -1), (-1, 1), (-1, -1)]
STEPS4 = [(dx, dy) for dx in range(-4, 5) for dy in range(-4, 5) if abs(dx) + abs(dy) == 4]


def shapes(max_moves):
    out = set()
    def rec(path, moves, used4):
        if len(path) == 8:
            last = path[-1]
            d = abs(last[0]) + abs(last[1])
            if d in (2, 4) and (d == 2 or not used4) and moves + d <= max_moves:
                # chiudi
                pts = path
                if valid(pts):
                    out.add(canon(pts))
            return
        for st in STEPS2 + ([] if used4 else STEPS4):
            d = abs(st[0]) + abs(st[1])
            if moves + d > max_moves - 2:
                continue
            q = (path[-1][0] + st[0], path[-1][1] + st[1])
            if q in path:
                continue
            rec(path + [q], moves + d, used4 or d == 4)
    def valid(pts):
        s = set(pts)
        for p in pts:
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (p[0] + d[0], p[1] + d[1]) in s:
                    return False
        return True
    def canon(pts):
        # normalizza: tutte le simmetrie del quadrato + rotazioni/riflessioni del ciclo
        best = None
        for sym in range(8):
            def f(p):
                x, y = p
                if sym & 1: x = -x
                if sym & 2: y = -y
                if sym & 4: x, y = y, x
                return (x, y)
            q = [f(p) for p in pts]
            for rot in range(8):
                for rev in (False, True):
                    r = q[rot:] + q[:rot]
                    if rev: r = r[::-1]
                    mx = min(p[0] for p in r); my = min(p[1] for p in r)
                    r = tuple((p[0] - mx, p[1] - my) for p in r)
                    if best is None or r < best: best = r
        return best
    rec([(0, 0)], 0, False)
    return out


def lattices():
    for n in (1, 2, 4, 8, 16, 32):
        m = 32 // n
        for k in range(n):
            yield (n, 0), (k, m)


def pack(shape, v1, v2):
    tours = []
    seen = set()
    n = 32
    # genera 32 traslati distinti
    for i in range(32):
        for j in range(32):
            ox = v1[0] * i + v2[0] * j; oy = v1[1] * i + v2[1] * j
            key = (ox % S, oy % S)
            if key in seen: continue
            seen.add(key)
            tours.append([wrap((x + ox, y + oy)) for (x, y) in shape])
            if len(tours) == 32: return tours
    return tours


def quick_valid(tours):
    trees = set()
    for tr in tours:
        for p in tr:
            if p in trees: return False
            trees.add(p)
    for p in trees:
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if wrap((p[0] + d[0], p[1] + d[1])) in trees: return False
    return True


if __name__ == "__main__":
    max_moves = int(sys.argv[1]) if len(sys.argv) > 1 else 18
    sh = shapes(max_moves)
    print("forme:", len(sh), file=sys.stderr)
    res = []
    for shape in sh:
        for v1, v2 in lattices():
            tours = pack(list(shape), v1, v2)
            if len(tours) != 32 or not quick_valid(tours): continue
            for both in (False, True):
                a = analyze(tours, both_routes=both, verbose=False)
                # costo stimato: mosse*200 + reroll (fix) + costo fix (~ P*2/3 su accettati * ~200)
                p = a['pacc']
                tot = a['tot']; n = 256
                fixfrac = (tot['P'] / 3) / (tot['G'] / 3 + tot['P'] * 2 / 3) if p > 0 else 0
                cost = 200 * a['moves'] + 403 * (1 / p - 1) + fixfrac * 200 * 1.5
                cost_static = 200 * a['moves'] + 403 * (1 / a['pstat'] - 1)
                res.append((cost, cost_static, a['moves'], tot, both, shape, v1, v2))
    res.sort(key=lambda r: r[0])
    seen = set()
    k = 0
    for r in res:
        key = (r[5], r[6], r[7])
        print("cost %.0f static %.0f moves %.3f T %.2f P %.2f F %.2f X %.2f G %.2f both=%d shape=%s v1=%s v2=%s" % (
            r[0], r[1], r[2], r[3]['T'] / 256, r[3]['P'] / 256, r[3]['F'] / 256, r[3]['X'] / 256, r[3]['G'] / 256, r[4], list(r[5]), r[6], r[7]))
        k += 1
        if k >= 25: break
    print("--- migliori statici ---")
    res.sort(key=lambda r: r[1])
    for r in res[:8]:
        print("static %.0f cost %.0f moves %.3f T %.2f shape=%s v1=%s v2=%s" % (r[1], r[0], r[2], r[3]['T'] / 256, list(r[5]), r[6], r[7]))
