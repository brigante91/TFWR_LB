#!/usr/bin/env python3
"""Predizione PURA (offline) della sequenza di companion che hay_probe stampera'
per un seed esplicito noto, da confrontare con l'output di gioco.

Modello:
  - randomPoly = DotNetRandom(derive_seeds(seed)["poly"])          (Simulation::.ctor)
  - startup: everythingUnlocked -> il mondo viene rigenerato 1x1 -> 1x3 -> 32x32,
    ogni ClearGrid mette erba su ogni cella consumando un companion (Farm::Unlock).
  - poi il drone legge il companion della sua cella e harvesta N-1 volte: ogni harvest
    ricrea l'erba => un nuovo ChooseCompanion.

Uso:
  python3 predict_poly.py [SEED] [PX PY] [N]
  default: SEED=746272860  cella=(0,0)  N=25
Confronta riga-per-riga con l'output 'c (Entities.X, (x, y))' di hay_probe.
Se NON combacia dalla prima riga: la sequenza di startup e'/l'ordine di clear e' diverso
-> usa il tuo match_poly.py che calibra l'offset automaticamente, poi me lo dici.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tfwr_rng import DotNetRandom, derive_seeds, choose_companion, clear_grid  # noqa: E402

STARTUP_SIZES = [(1, 1), (1, 3), (32, 32)]  # hay multi, confermato [gioco]
FINAL = (32, 32)
NAME = {"grass": "Grass", "bush": "Bush", "carrot": "Carrot", "tree": "Tree"}


def main():
    a = sys.argv[1:]
    seed = int(a[0]) if len(a) >= 1 else 746272860
    px = int(a[1]) if len(a) >= 3 else 0
    py = int(a[2]) if len(a) >= 3 else 0
    n = int(a[3]) if len(a) >= 4 else 25

    poly = DotNetRandom(derive_seeds(seed)["poly"])

    # --- startup: rigenerazioni del mondo, contando le estrazioni ---
    before = list(poly.sa), poly.inext, poly.inextp
    grid = {}
    for world in STARTUP_SIZES:
        grid = clear_grid(poly, world)
    # la cella del drone ha gia' un companion dallo startup (ultimo ClearGrid)
    if (px, py) not in grid:
        sys.exit(f"cella ({px},{py}) fuori dal mondo finale {FINAL}; passa PX PY corretti")

    print(f"seed={seed}  cella=({px},{py})  mondo={FINAL}  startup={STARTUP_SIZES}")
    seq = [grid[(px, py)]]
    for _ in range(n - 1):
        seq.append(choose_companion(poly, (px, py), "grass", FINAL))

    for t, (cx, cy) in seq:
        print(f"c (Entities.{NAME[t]}, ({cx}, {cy}))")


if __name__ == "__main__":
    main()
