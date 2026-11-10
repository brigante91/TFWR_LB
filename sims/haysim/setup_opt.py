"""Ottimizza l'avvio: ordine dei blocchi, orientamento della serpentina e punti di split dello spawn.

Costo misurato in azioni (200 tick). Un drone nato al tempo t nella posizione del genitore
parte al tempo t+1 (spawn = 1 azione del genitore).
Orientamenti: l'erba sta in uno dei 4 angoli del blocco 4x8; la serpentina parte dall'angolo
opposto sul lato corto lontano e finisce sull'erba.
"""
import random, statistics, itertools

S = 32


def dist(a, b):
    dx = (b[0] - a[0]) % S
    dy = (b[1] - a[1]) % S
    return min(dx, S - dx) + min(dy, S - dy)


def block_origin(b):
    i = b % 8
    return 4 * i, (8 * (b // 8) + 4 * (i % 2)) % S


def entries(b):
    """Punti d'ingresso possibili (uno per orientamento): (ingresso, orientamento)."""
    bx, by = block_origin(b)
    # o = (fx, fy): fx=0 erba a sinistra, fy=0 erba in basso
    out = []
    for fx in (0, 1):
        for fy in (0, 1):
            ex = bx if fx == 0 else bx + 3
            ey = by + 7 if fy == 0 else by
            out.append(((ex % S, ey % S), (fx, fy)))
    return out


def evaluate(order, wps):
    """order: lista di blocchi (indice drone -> blocco). wps: dict (lo,hi)->waypoint o None.
    Ritorna arrivi (in azioni) e orientamenti scelti."""
    arr = [0] * 32
    ori = [None] * 32

    def rr(lo, hi, pos, t):
        while hi - lo > 1:
            wp = wps.get((lo, hi))
            if wp is not None:
                t += dist(pos, wp)
                pos = wp
            mid = (lo + hi) // 2
            t += 1
            rr(mid, hi, pos, t)
            hi = mid
        b = order[lo]
        best = min(entries(b), key=lambda e: dist(pos, e[0]))
        arr[lo] = t + dist(pos, best[0])
        ori[lo] = best[1]

    rr(0, 32, (0, 0), 0)
    return arr, ori


def nodes():
    out = []
    def rr(lo, hi):
        while hi - lo > 1:
            out.append((lo, hi))
            mid = (lo + hi) // 2
            rr(mid, hi)
            hi = mid
    rr(0, 32)
    return out


def score(order, wps):
    return statistics.mean(evaluate(order, wps)[0])


def optimize(seed=0, iters=4000):
    rng = random.Random(seed)
    order = list(range(32))
    rng.shuffle(order)
    wps = {}
    cur = score(order, wps)
    ns = nodes()
    for it in range(iters):
        if rng.random() < 0.5:
            i, j = rng.randrange(32), rng.randrange(32)
            order[i], order[j] = order[j], order[i]
            new = score(order, wps)
            if new <= cur:
                cur = new
            else:
                order[i], order[j] = order[j], order[i]
        else:
            n = rng.choice(ns)
            old = wps.get(n)
            if old is None or rng.random() < 0.3:
                cand = (rng.randrange(S), rng.randrange(S))
            else:
                cand = ((old[0] + rng.randint(-2, 2)) % S, (old[1] + rng.randint(-2, 2)) % S)
            if rng.random() < 0.1:
                cand = None
            wps[n] = cand
            new = score(order, wps)
            if new <= cur:
                cur = new
            else:
                wps[n] = old
    return cur, order, {k: v for k, v in wps.items() if v is not None}


if __name__ == "__main__":
    base = score(list(range(32)), {})
    print("attuale (con orientamento scelto)", base)
    best = None
    for s in range(12):
        r = optimize(s, 20000)
        print(s, r[0])
        if best is None or r[0] < best[0]:
            best = r
    print("BEST", best[0])
    print("ORDER", best[1])
    print("WPS", best[2])
    arr, ori = evaluate(best[1], best[2])
    print("ARR", arr, "max", max(arr))
    print("ORI", ori)
