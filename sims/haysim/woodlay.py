"""Layout per lb_wood_v2: 32 giri indipendenti da 8 alberi.
Per ogni giro: celle degli alberi in ordine; per ogni passo le celle attraversate (percorso a L:
prima x poi y = route 0; prima y poi x = route 1).  Valuta: mosse, alberi nel rombo (T),
celle del proprio percorso nel rombo (P), celle di percorsi altrui nel rombo (F), resto (G)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
S = 32
DIAMOND = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) if (dx or dy) and abs(dx) + abs(dy) <= 3]


def wrap(p):
    return (p[0] % S, p[1] % S)


def sdelta(a, b):
    d = (b - a) % S
    return d if d <= S // 2 else d - S


def route_cells(a, b, r):
    """celle intermedie (escluse a e b) del percorso a L da a a b: r=0 x prima, r=1 y prima."""
    dx = sdelta(a[0], b[0]); dy = sdelta(a[1], b[1])
    sx = 1 if dx > 0 else -1; sy = 1 if dy > 0 else -1
    cells = []
    x, y = a
    if r == 0:
        for _ in range(abs(dx)):
            x += sx; cells.append(wrap((x, y)))
        for _ in range(abs(dy)):
            y += sy; cells.append(wrap((x, y)))
    else:
        for _ in range(abs(dy)):
            y += sy; cells.append(wrap((x, y)))
        for _ in range(abs(dx)):
            x += sx; cells.append(wrap((x, y)))
    return cells[:-1]


def dist(a, b):
    return abs(sdelta(a[0], b[0])) + abs(sdelta(a[1], b[1]))


RING8 = [(1, 0), (3, 0), (5, 0), (6, 1), (5, 2), (3, 2), (1, 2), (0, 1)]
OCT8 = [(1, 0), (3, 0), (4, 1), (4, 3), (3, 4), (1, 4), (0, 3), (0, 1)]


def shape_tours(shape, v1, v2, n1, n2, flip_alt=False):
    tours = []
    for i in range(n1):
        for j in range(n2):
            ox = v1[0] * i + v2[0] * j; oy = v1[1] * i + v2[1] * j
            sh = shape
            if flip_alt and j % 2:
                sh = [(x, 2 * 1 - y) if max(q[1] for q in shape) == 2 else (x, 4 - y) for (x, y) in shape]
            tours.append([wrap((x + ox, y + oy)) for (x, y) in sh])
    return tours


def ladder_tours():
    tours = []
    for c in range(0, S, 8):
        for y0 in range(0, S, 4):
            A = [wrap((y0 + i + c, y0 + i)) for i in range(4)]
            B = [wrap((y0 + i + c + 4, y0 + i)) for i in reversed(range(4))]
            tours.append(A + B)
    return tours


def analyze(tours, both_routes=True, verbose=True, name=""):
    trees = {}
    for ti, tr in enumerate(tours):
        for p in tr:
            assert p not in trees, ("doppione", p)
            trees[p] = ti
    assert len(trees) == 256, len(trees)
    # adiacenza
    for p in trees:
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            assert wrap((p[0] + d[0], p[1] + d[1])) not in trees, ("adiacenti", p)
    paths = []   # per giro: set di celle di percorso (default) e alternative
    moves = 0
    for tr in tours:
        dflt = set(); alt = set()
        for k in range(len(tr)):
            a = tr[k]; b = tr[(k + 1) % len(tr)]
            moves += dist(a, b)
            dflt |= set(route_cells(a, b, 0))
            alt |= set(route_cells(a, b, 1))
        paths.append((dflt, alt))
    owner = {}
    for ti, (d, a) in enumerate(paths):
        for q in (d | a) if both_routes else d:
            owner.setdefault(q, set()).add(ti)
    tot = dict(T=0, P=0, F=0, G=0, X=0)
    per = []
    for p, ti in trees.items():
        c = dict(T=0, P=0, F=0, G=0, X=0)
        mine = (paths[ti][0] | paths[ti][1]) if both_routes else paths[ti][0]
        for (dx, dy) in DIAMOND:
            q = wrap((p[0] + dx, p[1] + dy))
            if q in trees:
                c['T'] += 1
            elif q in mine:
                if len(owner[q]) == 1:
                    c['P'] += 1
                else:
                    c['X'] += 1      # mio ma anche di altri: non affidabile
            elif q in owner:
                c['F'] += 1
            else:
                c['G'] += 1
        for k in c: tot[k] += c[k]
        per.append(c)
    n = len(trees)
    # p accettazione: G/3 + P*2/3 (erba o cespuglio) su 24
    pacc = (tot['G'] / 3 + tot['P'] * 2 / 3) / (24 * n)
    pstat = (tot['G'] + tot['P'] + tot['F'] + tot['X']) / 3 / (24 * n)
    if verbose:
        print("%-28s mosse/albero %.3f  T %.2f P %.2f F %.2f X %.2f G %.2f | p_fix %.3f (rr %.2f)  p_static %.3f (rr %.2f)" % (
            name, moves / n, tot['T'] / n, tot['P'] / n, tot['F'] / n, tot['X'] / n, tot['G'] / n,
            pacc, 1 / pacc - 1, pstat, 1 / pstat - 1))
    return dict(moves=moves / n, tot=tot, pacc=pacc, pstat=pstat, trees=trees, paths=paths)


LAYOUTS = {
    "ladder m=4": ladder_tours,
    "ring8 (8,0)x(0,4)": lambda: shape_tours(RING8, (8, 0), (0, 4), 4, 8),
    "ring8 (8,0)x(4,4)": lambda: shape_tours(RING8, (8, 0), (4, 4), 4, 8),
    "ring8 (8,0)x(2,4)": lambda: shape_tours(RING8, (8, 0), (2, 4), 4, 8),
    "oct8 (8,0)x(4,4)": lambda: shape_tours(OCT8, (8, 0), (4, 4), 4, 8),
    "oct8 (8,0)x(-4,4)": lambda: shape_tours(OCT8, (8, 0), (-4, 4), 4, 8),
    "oct8 (8,0)x(2,4)": lambda: shape_tours(OCT8, (8, 0), (2, 4), 4, 8),
    "oct8 (8,0)x(6,4)": lambda: shape_tours(OCT8, (8, 0), (6, 4), 4, 8),
    "oct8 (8,4)x(0,8)?": lambda: shape_tours(OCT8, (8, 4), (0, 8), 4, 8),
    "oct8 (4,8)x(8,0)": lambda: shape_tours(OCT8, (4, 8), (8, 0), 4, 8),
}

if __name__ == "__main__":
    for name, fn in LAYOUTS.items():
        try:
            tours = fn()
            analyze(tours, both_routes=True, name=name)
            analyze(tours, both_routes=False, name=name + " [1 route]")
        except AssertionError as e:
            print("%-28s NON VALIDO: %s" % (name, e))
