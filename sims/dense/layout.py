"""Disposizione densa delle coppie d'erba: reticolo (6,0),(3,2), 32 coppie vicino all'origine."""
S = 32
D = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) if (dx or dy) and abs(dx) + abs(dy) <= 3]


def wrapd(a, b):
    d = abs(a - b) % S
    return min(d, S - d)


def dist(p, q):
    return wrapd(p[0], q[0]) + wrapd(p[1], q[1])


def pairs_near(cx, cy, n=32, metric=None):
    pts = []
    for a in range(-8, 9):
        for b in range(-12, 13):
            x = 6 * a + 3 * b + cx
            y = 2 * b + cy
            pts.append((x, y))
    metric = metric or (lambda p: abs(p[0] + 0.5 - cx) + 1.6 * abs(p[1] - cy))
    pts.sort(key=metric)
    return [((x % S, y % S), ((x + 1) % S, y % S)) for x, y in pts[:n]]


def analyse(pairs):
    grass = set(c for pr in pairs for c in pr)
    assert len(grass) == 2 * len(pairs)
    union = set()
    bad = 0
    for g in grass:
        for dx, dy in D:
            c = ((g[0] + dx) % S, (g[1] + dy) % S)
            if c in grass:
                bad += 1
            else:
                union.add(c)
    return grass, union, bad


if __name__ == "__main__":
    best = None
    for cx in range(-3, 4):
        for cy in range(-2, 3):
            for k in (1.0, 1.3, 1.6, 2.0, 2.5):
                pr = pairs_near(cx, cy, metric=lambda p, k=k, cx=cx, cy=cy: abs(p[0] + 0.5 - cx) + k * abs(p[1] - cy))
                g, u, bad = analyse(pr)
                if bad != 64:   # ogni erba deve vedere solo la propria compagna
                    continue
                if best is None or len(u) < best[0]:
                    best = (len(u), cx, cy, k, pr)
    n, cx, cy, k, pr = best
    print("cespugli totali", n, "per drone %.1f" % (n / 32), "(attuale: 960, 30 per drone)")
    g, u, bad = analyse(pr)
    xs = sorted(set(c[0] for c in u | g)); ys = sorted(set(c[1] for c in u | g))
    print("celle usate", len(u) + len(g))
    import json
    json.dump({"pairs": pr}, open("pairs.json", "w"))
    # mappa
    for y in range(S - 1, -1, -1):
        print("".join("G" if (x, y) in g else ("b" if (x, y) in u else ".") for x in range(S)))
