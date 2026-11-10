#!/usr/bin/env python3
"""Simulatore tick-exact (per-drone) del ciclo hay di lb_hay.

Costi (op) dal decompilato:
  harvest/plant/till/move/use_item(water) riusciti = 200 op ; osservazioni = 1 op.
  move con straw_hat = 200 (Hat.OnMove base = -1 -> 200).
Resa erba: boosted = 81920, unboosted = 512 (grass 10 -> 512, polyculture 5 -> x160).
Crescita erba: 0.5/(1+4*water) s. Velocita' max: OpDuration = 164610 ns/op.

Modella il loop di harvest_poly_hay: 1 harvest produttivo + re-roll (harvest finche'
companion == bush e pos != avoid), alternando 2 celle (west/east) con 1 move tra loro.
Il flusso poly reale (da un seed) decide fit/no-fit di ogni companion.

Uso: python3 hay_sim.py [SEED] [CYCLES]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tfwr_rng import DotNetRandom, derive_seeds, choose_companion, clear_grid  # noqa: E402

OP_NS = 2_500_000 / 15.1875          # ns per op a speed max (= 164610.4)
WORLD = (32, 32)
STARTUP = [(1, 1), (1, 3), (32, 32)]
BOOSTED, UNBOOSTED = 81920, 512
WATER = 0.68


def grow_ops(w):
    grow_s = 0.5 / (1.0 + 4.0 * w)
    return grow_s * 1e9 / OP_NS


def sim_drone(seed, cycles, water=WATER):
    """Simula un drone su 2 celle grass (west/east) con contorno bush.
    Ritorna dict con op totali, harvest produttivi, re-roll, move, idle, hay."""
    poly = DotNetRandom(derive_seeds(seed)["poly"])
    clear_grid(poly, (1, 1)); clear_grid(poly, (1, 3)); clear_grid(poly, WORLD)  # startup

    # due celle vicine; companion valido = tipo bush e companionPos != l'altra cella
    west = (0, 0)
    east = (1, 0)
    cells = {west: east, east: west}   # cella -> avoid
    gready = {west: 0.0, east: 0.0}    # op a cui la cella e' matura

    ops = 0.0
    n_prod = n_reroll = n_move = 0
    idle = 0.0
    hay = 0
    pos = west
    g = grow_ops(water)

    def companion_is_bush(cell, avoid):
        t, p = choose_companion(poly, cell, "grass", WORLD)
        return t == "bush" and p != avoid

    # all'avvio ogni cella ha gia' un companion (startup) -> assumiamo non-bush (peggiore)
    # (dettaglio minore: il primo ciclo e' un transiente)
    sat = {west: False, east: False}

    order = [west, east]
    oi = 0
    for _ in range(cycles):
        cell = order[oi % 2]; avoid = cells[cell]; oi += 1
        # muovi sulla cella se non ci sei
        if pos != cell:
            ops += 200; n_move += 1; pos = cell
        # aspetta che sia matura (can_harvest in loop = 1 op ciascuno; idle = attesa)
        if ops < gready[cell]:
            idle += gready[cell] - ops
            ops = gready[cell]
        # harvest produttivo: boosted se la cella era 'sat' (companion bush dal ciclo prec.)
        ops += 200; n_prod += 1
        hay += BOOSTED if sat[cell] else UNBOOSTED
        # re-roll: harvest finche' companion == bush (prepara il boost del PROSSIMO giro)
        while True:
            ops += 1  # get_companion
            if companion_is_bush(cell, avoid):
                sat[cell] = True
                break
            sat[cell] = False
            ops += 200; n_reroll += 1   # harvest di re-roll (erba acerba, 0 resa)
        gready[cell] = ops + g  # ricresce dopo l'ultimo harvest
    t_s = ops * OP_NS / 1e9
    return dict(ops=ops, sec=t_s, prod=n_prod, reroll=n_reroll, move=n_move,
                idle_ops=idle, hay=hay, ops_per_prod=ops / n_prod)


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 746272860
    cycles = int(sys.argv[2]) if len(sys.argv) > 2 else 4000
    r = sim_drone(seed, cycles)
    GOAL = 2_000_000_000
    DRONES = 32
    # throughput a regime: hay per op (su cicli a regime), tempo per 32 droni in parallelo
    hay_per_op = r["hay"] / r["ops"]
    ops_needed = GOAL / DRONES / hay_per_op
    t_total_s = ops_needed * OP_NS / 1e9
    print(f"seed={seed} cicli={cycles}")
    print(f"  harvest produttivi={r['prod']}  re-roll={r['reroll']}  move={r['move']}")
    print(f"  op totali={r['ops']:.0f}  di cui idle={r['idle_ops']:.0f} "
          f"({100*r['idle_ops']/r['ops']:.1f}%)")
    print(f"  op per harvest produttivo = {r['ops_per_prod']:.1f}")
    print(f"  re-roll medi per harvest produttivo = {r['reroll']/r['prod']:.2f}")
    print(f"  hay/op = {hay_per_op:.1f}")
    print(f"  --> tempo stimato 32 droni per {GOAL:,} hay: {t_total_s:.1f}s "
          f"= {int(t_total_s//60)}:{t_total_s%60:05.2f}")
    print(f"      (escluso setup iniziale del campo)")


if __name__ == "__main__":
    main()
