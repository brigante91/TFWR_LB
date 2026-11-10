#!/usr/bin/env python3
"""Baseline re-roll generalizzato: K celle d'erba (layout qualsiasi) + acqua variabile.
Obiettivo: azzerare l'idle (attesa crescita) scegliendo layout/acqua -> scendere sotto 1:50.

Modello (fedele a lb_hay):
  - bush ovunque tranne le celle d'erba del layout.
  - ciclo per cella: harvest produttivo (boosted se il companion attuale e' bush valido),
    poi re-roll IN LOCO (harvest finche' companion==bush e pos non e' erba) -> prepara il
    boost del prossimo giro. Costo harvest/move 200, osservazione 1.
  - il drone va sempre sulla cella MATURA piu' vicina (nearest grown) per minimizzare idle.
Resa boosted 81920 / unboosted 512. Crescita 0.5/(1+4*water) s. OpDuration 164610 ns.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tfwr_rng import DotNetRandom, derive_seeds, choose_companion, clear_grid  # noqa: E402

OP_NS = 2_500_000 / 15.1875
WORLD = (32, 32)
BOOSTED, UNBOOSTED = 81920, 512

LAYOUTS = {
    "lbhay_2":   [(0, 0), (1, 0)],
    "line_3":    [(0, 0), (1, 0), (2, 0)],
    "line_4":    [(0, 0), (1, 0), (2, 0), (3, 0)],
    "square_2x2":[(0, 0), (1, 0), (0, 1), (1, 1)],
    "ring_4":    [(0, 0), (1, 0), (1, 1), (0, 1)],   # ciclo: ritorno in 1 passo
    "spaced_3":  [(0, 0), (2, 0), (4, 0)],
}


def sim(layout, seed, water, cycles=4000):
    poly = DotNetRandom(derive_seeds(seed)["poly"])
    clear_grid(poly, (1, 1)); clear_grid(poly, (1, 3)); clear_grid(poly, WORLD)
    grass = set(layout)
    grow = (0.5 / (1 + 4 * water)) * 1e9 / OP_NS
    ready = {c: 0.0 for c in layout}
    setup = {c: False for c in layout}
    ops = 0.0; hay = 0; pos = layout[0]
    n_prod = n_rr = n_move = 0; idle = 0.0

    def valid_bush():
        t, p = choose_companion(poly, pos, "grass", WORLD)
        return t == "bush" and p not in grass

    def d(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    for _ in range(cycles):
        grown = [c for c in layout if ready[c] <= ops]
        if not grown:
            nxt = min(ready.values()); idle += nxt - ops; ops = nxt
            grown = [c for c in layout if ready[c] <= ops]
        # cella matura piu' vicina, preferendo quelle gia' setup (boost)
        c = min(grown, key=lambda z: (0 if setup[z] else 1, d(pos, z)))
        if pos != c:
            ops += 200 * d(pos, c); n_move += d(pos, c)
        pos = c
        ops += 200; n_prod += 1           # harvest produttivo
        hay += BOOSTED if setup[c] else UNBOOSTED
        # re-roll in loco finche' companion bush valido
        while True:
            ops += 1
            if valid_bush():
                setup[c] = True; break
            setup[c] = False
            ops += 200; n_rr += 1
        ready[c] = ops + grow

    hay_per_op = hay / ops
    t = (2_000_000_000 / 32 / hay_per_op) * OP_NS / 1e9
    return dict(t=t, opb=ops / n_prod, rr=n_rr / n_prod,
                mv=n_move / n_prod, idle=100 * idle / ops)


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 746272860
    print(f"{'layout':12} {'water':>5} {'op/boost':>9} {'rr':>5} {'mv':>5} {'idle%':>6} {'tempo':>9}")
    for water in (0.68, 1.0):
        for name, lay in LAYOUTS.items():
            r = sim(lay, seed, water)
            mm = f"{int(r['t']//60)}:{r['t']%60:05.2f}"
            print(f"{name:12} {water:5.2f} {r['opb']:9.1f} {r['rr']:5.2f} "
                  f"{r['mv']:5.2f} {r['idle']:6.1f} {mm:>9}")
        print()


if __name__ == "__main__":
    main()
