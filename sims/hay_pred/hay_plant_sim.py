#!/usr/bin/env python3
"""Metodo 'pianta il companion richiesto' (no re-roll) con campo companion persistente.

Per ogni erba: harvest (boosted, perche' il companion e' stato piazzato), get_companion (T,P),
e se la cella P non ha gia' tipo T -> un piazzatore ci va e pianta T (move+plant). Riuso quando
P ha gia' T. Ogni harvest e' boostato al 100%.

Conta il lavoro TOTALE (harvest + companion) e stima il tempo con 32 droni in parallelo
(harvester + piazzatori, lavoro bilanciabile -> tempo ~ lavoro_totale/32).

NB: stima di prototipo; la vera implementazione ha overhead di coordinamento (send/spawn).
Uso: python3 hay_plant_sim.py [SEED] [NGRASS] [CYCLES]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tfwr_rng import DotNetRandom, derive_seeds, choose_companion, clear_grid  # noqa: E402

OP_NS = 2_500_000 / 15.1875
WORLD = (32, 32)
BOOSTED = 81920


def wdist(a, b):
    dx = min((a[0] - b[0]) % 32, (b[0] - a[0]) % 32)
    dy = min((a[1] - b[1]) % 32, (b[1] - a[1]) % 32)
    return dx + dy


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 746272860
    ngrass = int(sys.argv[2]) if len(sys.argv) > 2 else 16
    cycles = int(sys.argv[3]) if len(sys.argv) > 3 else 8000

    poly = DotNetRandom(derive_seeds(seed)["poly"])
    clear_grid(poly, (1, 1)); clear_grid(poly, (1, 3)); clear_grid(poly, WORLD)

    # celle d'erba sparse su una colonna (grass ogni 4 per non inquinare troppo i companionPos)
    grass_cells = [(5, 1 + 2 * i) for i in range(ngrass)]
    field = {}            # pos -> tipo companion piazzato (persistente)

    harvest_ops = 0.0     # lavoro degli harvester
    comp_ops = 0.0        # lavoro dei piazzatori
    n_boost = 0
    n_plant = 0
    reuse = 0

    gi = 0
    for _ in range(cycles):
        g = grass_cells[gi % ngrass]; gi += 1
        # harvest boostato + get_companion + send richiesta a un helper
        harvest_ops += 200 + 1 + 1    # harvest + get_companion + send
        n_boost += 1
        # nuovo companion richiesto dalla ricrescita
        t, p = choose_companion(poly, g, "grass", WORLD)
        if field.get(p) == t:
            reuse += 1                # gia' presente: gratis
        else:
            # helper persistente stazionato nella zona: receive + move (solo andata) + plant
            # move dall'helper a p: approssimo con la distanza companionPos (helper vicino al plot)
            comp_ops += 1 + wdist(g, p) * 200 + 200   # recv + move andata + plant
            field[p] = t
            n_plant += 1

    total = harvest_ops + comp_ops
    opb = total / n_boost
    reuse_pct = 100 * reuse / n_boost
    # tempo con 32 droni, lavoro bilanciato
    t_bal = (BOOSTED and (2_000_000_000 / BOOSTED)) * opb / 32 * OP_NS / 1e9
    print(f"seed={seed} ngrass={ngrass} cicli={cycles}")
    print(f"  harvest_ops={harvest_ops:.0f}  comp_ops={comp_ops:.0f}  piazzamenti={n_plant} "
          f"riuso={reuse_pct:.1f}%")
    print(f"  op per boost (harvest+companion) = {opb:.1f}")
    print(f"  --> stima 32 droni (lavoro/32): {t_bal:.1f}s = {int(t_bal//60)}:{t_bal%60:05.2f}")
    print(f"      (baseline lb_hay = 1:50; floor re-roll = ~1:44)")


if __name__ == "__main__":
    main()
