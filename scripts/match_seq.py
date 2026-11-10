"""
Secondo test: misura QUANTI companion consuma ogni azione.

Uso:
  python match_seq.py SEED output_gioco.txt

L'output del gioco contiene righe etichettate, nell'ordine:
  pos X Y S N
  P0 (Entities.Tree, (x, y))
  P1 (...)
  ...
Per ogni fase lo script trova quanti companion "invisibili" sono stati estratti
tra l'osservazione precedente e questa (k). Regole validate:
flusso poly, r=3, x poi y, riestrae (0,0) e distanza Manhattan > 3, tipo != Grass.
"""
import re
import sys

from tfwr_rng import SimulationRng, INV_MBIG

TYPES = ["Grass", "Bush", "Carrot", "Tree"]
R = 3
POOL = 40000


def nxt(raw, i, lo, hi):
    return int(raw[i] * INV_MBIG * (hi - lo)) + lo


def one(raw, i):
    while True:
        dx = nxt(raw, i, -R, R + 1)
        dy = nxt(raw, i + 1, -R, R + 1)
        i += 2
        if (dx == 0 and dy == 0) or abs(dx) + abs(dy) > R:
            continue
        break
    while True:
        t = nxt(raw, i, 0, 4)
        i += 1
        if t != 0:
            break
    return (TYPES[t], dx, dy), i


def parse(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"pos\D*?(-?\d+)\D+?(-?\d+)\D+?S\D*?(\d+)", text)
    x0, y0, size = int(m.group(1)), int(m.group(2)), int(m.group(3))
    obs = []
    extra = []
    for line in text.splitlines():
        mm = re.match(r"\s*(A|P\d+)\D.*?Entities\.(\w+)\s*,\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", line)
        if mm:
            dx = (int(mm.group(3)) - x0 + size // 2) % size - size // 2
            dy = (int(mm.group(4)) - y0 + size // 2) % size - size // 2
            obs.append((mm.group(1), (mm.group(2), dx, dy)))
        elif "tick" in line:
            extra.append(line.strip())
    return obs, extra


def main():
    seed = int(sys.argv[1])
    obs, extra = parse(sys.argv[2])
    rnd = SimulationRng(seed).poly
    raw = [rnd.sample() for _ in range(POOL)]

    # allineamento: le righe "A" sono raccolti consecutivi (nessuna azione in mezzo)
    align = [ev for label, ev in obs if label == "A"]
    phases = [(label, ev) for label, ev in obs if label != "A"]
    if len(align) < 5:
        sys.exit("Servono almeno 5 righe A di allineamento.")
    pos = None
    for off in range(30000):
        i = off
        ok = True
        for a in align:
            ev, i = one(raw, i)
            if ev != a:
                ok = False
                break
        if ok:
            pos = i
            break
    if pos is None:
        sys.exit("Allineamento non trovato nel flusso poly.")
    print(f"Allineato su {len(align)} raccolti consecutivi (estrazione {off})")

    prev = align[-1]
    for label, ev in phases:
        if ev == prev:
            print(f"{label}: identico al precedente -> valore in cache, nessuna nuova estrazione")
            continue
        found = None
        i = pos
        for k in range(0, 40):
            got, end = one(raw, i)
            if got == ev:
                found = (k, end)
                break
            i = end
        same = " (uguale alla precedente)" if ev == prev else ""
        if found is None:
            print(f"{label}: NON trovato entro 40 companion{same} -> cache o regole diverse")
        else:
            k, end = found
            if k == 0 and same:
                print(f"{label}: k=0 ma identico al precedente: probabilmente valore in cache, nessuna estrazione")
            else:
                print(f"{label}: k={k} companion extra estratti prima di questo{same}")
                pos = end
        prev = ev
    if extra:
        print("\nCosti in tick:")
        for line in extra:
            print("  " + line)


if __name__ == "__main__":
    main()
