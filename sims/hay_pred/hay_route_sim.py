#!/usr/bin/env python3
"""Prototipo: hay con ROUTING guidato dalla predizione poly (niente re-roll a vuoto).

Confronto onesto col baseline re-roll. Modello (singolo drone):
  - griglia 32x32, companion a 3 colori su ogni cella: col=(x+2y)%3 -> bush/carrot/tree
  - celle d'erba su un sotto-reticolo rado (spacing SP) sovrascrivono il colore
  - boost se la companion della cella (tipo T, pos P) ha col(P)==T e P non e' erba
  - routing: tra le celle mature, scelgo (con PEEK sullo stream, senza consumarlo)
    quelle la cui ricrescita sara' fit -> ogni harvest produttivo e' boostato.
Costi: harvest 200, move 200/passo, osservazione 1. Resa boosted 81920 / unboosted 512.

NB: stima di prototipo (singolo drone, layout semplice), non bit-exact del run 32-droni.
Uso: python3 hay_route_sim.py [SEED] [SP] [REGION] [STEPS]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tfwr_rng import DotNetRandom, derive_seeds, choose_companion, clear_grid  # noqa: E402

OP_NS = 2_500_000 / 15.1875
WORLD = (32, 32)
BOOSTED, UNBOOSTED = 81920, 512
TYPES = ["bush", "carrot", "tree"]


def col(x, y):
    return TYPES[(x + 2 * y) % 3]


def clone(r):
    c = DotNetRandom.__new__(DotNetRandom)
    c.sa = list(r.sa); c.inext = r.inext; c.inextp = r.inextp
    return c


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 746272860
    sp = int(sys.argv[2]) if len(sys.argv) > 2 else 3        # spacing celle erba
    reg = int(sys.argv[3]) if len(sys.argv) > 3 else 12      # lato regione di lavoro
    steps = int(sys.argv[4]) if len(sys.argv) > 4 else 6000

    poly = DotNetRandom(derive_seeds(seed)["poly"])
    clear_grid(poly, (1, 1)); clear_grid(poly, (1, 3)); clear_grid(poly, WORLD)

    grass = [(x, y) for x in range(0, reg, sp) for y in range(0, reg, sp)]
    grass_set = set(grass)

    def fit_of(t, p):
        return (p not in grass_set) and (col(*p) == t)

    def peek(cell):
        g = clone(poly)
        t, p = choose_companion(g, cell, "grass", WORLD)
        return fit_of(t, p)

    w = 1.0  # acqua al massimo -> crescita veloce
    grow = (0.5 / (1 + 4 * w)) * 1e9 / OP_NS
    ready = {c: 0.0 for c in grass}
    setup = {c: False for c in grass}   # la companion attuale e' boostata?

    ops = 0.0; hay = 0; pos = grass[0]
    n_harv = n_boost = n_move = 0; idle = 0.0

    def dist(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    for _ in range(steps):
        grown = [c for c in grass if ready[c] <= ops]
        if not grown:
            nxt = min(ready.values()); idle += nxt - ops; ops = nxt
            grown = [c for c in grass if ready[c] <= ops]
        # preferisci: boostata adesso E ricrescita fit, piu' vicina
        def score(c):
            return (0 if (setup[c] and peek(c)) else 1 if setup[c] else 2 if peek(c) else 3,
                    dist(pos, c))
        c = min(grown, key=score)
        if pos != c:
            ops += 200 * dist(pos, c); n_move += dist(pos, c); pos = c
        ops += 1  # get_companion (per decidere) - modella il costo osservazione
        # harvest produttivo
        ops += 200; n_harv += 1
        if setup[c]:
            hay += BOOSTED; n_boost += 1
        else:
            hay += UNBOOSTED
        # ricrescita: consuma lo stream, determina il prossimo setup
        t, p = choose_companion(poly, c, "grass", WORLD)
        setup[c] = fit_of(t, p)
        ready[c] = ops + grow

    t_s = ops * OP_NS / 1e9
    hay_per_op = hay / ops
    GOAL, DRONES = 2_000_000_000, 32
    t_total = (GOAL / DRONES / hay_per_op) * OP_NS / 1e9
    print(f"seed={seed} spacing={sp} regione={reg}x{reg} celle_erba={len(grass)} steps={steps}")
    print(f"  harvest={n_harv}  boostati={n_boost} ({100*n_boost/n_harv:.1f}%)  "
          f"move_passi={n_move}  idle={100*idle/ops:.1f}%")
    print(f"  op per harvest = {ops/n_harv:.1f}   op per boost = {ops/max(n_boost,1):.1f}")
    print(f"  hay/op = {hay_per_op:.1f}")
    print(f"  --> tempo stimato 32 droni: {t_total:.1f}s = {int(t_total//60)}:{t_total%60:05.2f}")


if __name__ == "__main__":
    main()
