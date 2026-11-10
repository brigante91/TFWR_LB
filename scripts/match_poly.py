"""
Valida il predittore: confronta i companion osservati in gioco (simulate con seed
fisso) con quelli previsti da tfwr_rng.py, cercando automaticamente:
  - quale flusso li genera (dovrebbe essere "poly")
  - quante estrazioni sono state consumate prima (piante iniziali, ecc.)
  - il raggio r, l'ordine x/y, se (0,0) o fuori-raggio vengono riestratti

Uso:
  python match_poly.py SEED output_gioco.txt

output_gioco.txt = l'output copiato dalla console del gioco, con righe tipo
  pos 0 0 S 32
  c (Entities.Bush, (30, 31))
"""
import re
import sys
import itertools

from tfwr_rng import SimulationRng, STREAMS, INV_MBIG

TYPES = ["Grass", "Bush", "Carrot", "Tree"]  # ordine di Next(4) dal report
MAX_OFFSET = 30000
POOL = MAX_OFFSET + 5000


def parse(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"pos\D*?(-?\d+)\D+?(-?\d+)\D+?S\D*?(\d+)", text)
    if not m:
        sys.exit("Non trovo la riga 'pos X Y S N' nell'output.")
    x0, y0, size = int(m.group(1)), int(m.group(2)), int(m.group(3))
    obs = []
    for line in text.splitlines():
        if not line.strip().startswith("c "):
            continue
        mm = re.search(r"Entities\.(\w+)\s*,\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", line)
        if mm:
            t, x, y = mm.group(1), int(mm.group(2)), int(mm.group(3))
            dx = (x - x0 + size // 2) % size - size // 2
            dy = (y - y0 + size // 2) % size - size // 2
            obs.append((t, dx, dy))
    return obs


def nxt(raw, i, lo, hi):
    return int(raw[i] * INV_MBIG * (hi - lo)) + lo


def gen(raw, start, n, r, order, zero_redraw, manhattan):
    """Genera n companion per una pianta d'erba partendo dall'estrazione start."""
    i = start
    out = []
    for _ in range(n):
        while True:
            if i + 2 >= len(raw):
                return None, i
            a = nxt(raw, i, -r, r + 1)
            b = nxt(raw, i + 1, -r, r + 1)
            i += 2
            dx, dy = (a, b) if order == "xy" else (b, a)
            if zero_redraw and dx == 0 and dy == 0:
                continue
            if manhattan and abs(dx) + abs(dy) > r:
                continue
            break
        while True:
            if i >= len(raw):
                return None, i
            t = nxt(raw, i, 0, 4)
            i += 1
            if t != 0:  # riestratto se uguale al tipo della pianta (Grass)
                break
        out.append((TYPES[t], dx, dy))
    return out, i


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    seed = int(sys.argv[1])
    obs = parse(sys.argv[2])
    if len(obs) < 8:
        sys.exit(f"Servono almeno 8 companion osservati, ne ho trovati {len(obs)}.")
    print(f"Osservati {len(obs)} companion. Primi 5: {obs[:5]}")

    sim = SimulationRng(seed)
    found = []
    for stream in STREAMS:
        rnd = getattr(sim, stream)
        raw = [rnd.sample() for _ in range(POOL)]
        for r, order, zr, mh in itertools.product(range(1, 6), ("xy", "yx"), (True, False), (True, False)):
            first = obs[0]
            for off in range(MAX_OFFSET):
                ev, _ = gen(raw, off, 1, r, order, zr, mh)
                if ev is None or ev[0] != first:
                    continue
                ev, end = gen(raw, off, len(obs), r, order, zr, mh)
                if ev == obs:
                    found.append((stream, off, r, order, zr, mh, end))
    if not found:
        print("\nNessuna corrispondenza. Possibili cause: il companion usa estrazioni diverse"
              " da quelle ipotizzate, oppure altre azioni consumano il flusso tra un"
              " companion e l'altro. Incolla l'output e il codice di GetCompanion.")
        return
    print("\nCORRISPONDENZE TROVATE:")
    for stream, off, r, order, zr, mh, end in found:
        print(f"  flusso={stream} offset={off} r={r} ordine={order} "
              f"riestrae(0,0)={zr} limite_manhattan={mh} -> estrazioni usate {off}..{end}")


if __name__ == "__main__":
    main()
