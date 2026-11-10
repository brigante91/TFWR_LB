"""v5: partizioni con piu' campo (quadrati con corridoi, 2+ droni per quadrato), fusione reale dei gruppi.
Harvester = colonne di sinistra (2 o 3) del quadrato su un ciclo hamiltoniano che contiene (x0,y0) e la
cella di controllo (x0, y0+L-1): il riempimento parte dalla cella di controllo e vi torna.
Gli altri droni: serpentina per colonne sulle colonne restanti, tagliata in pezzi uguali (percorsi,
invertiti a ogni ciclo). Logica di riempimento di v4 (pump_blk.block_cycle)."""
import sys
from pumpsim import *
import pump_ind
from pump_ind import drone_prog, spawn_range, make_main, dist
import pump_blk

DEFAULT = dict(pump_ind.DEFAULT)


def cycle2(x0, y0, w, L):
    """ciclo hamiltoniano su w colonne x L righe (w=2 sempre; w=3 richiede L pari): colonna 0 in su,
    poi le righe a serpentina in giu' sulle colonne 1..w-1; l'ultima cella e' adiacente alla prima."""
    cells = [(x0, y0 + j) for j in range(L)]
    for j in range(L - 1, -1, -1):
        xs = range(1, w) if (L - 1 - j) % 2 == 0 else range(w - 1, 0, -1)
        for i in xs:
            cells.append((x0 + i, y0 + j))
    assert all(dist(a, b) == 1 for a, b in zip(cells, cells[1:])) and dist(cells[0], cells[-1]) == 1, (w, L)
    return cells


def chunks(x0, y0, c_from, L, ndr):
    """serpentina per colonne sulle colonne c_from..L-1, tagliata in ndr pezzi (quasi) uguali."""
    cells = []
    for i in range(c_from, L):
        ys = range(L) if (i - c_from) % 2 == 0 else range(L - 1, -1, -1)
        for j in ys:
            cells.append((x0 + i, y0 + j))
    n = len(cells)
    out, start = [], 0
    for k in range(ndr):
        m = n // ndr + (1 if k < n % ndr else 0)
        out.append(cells[start:start + m])
        start += m
    return out


def build(squares, ndrones, hcols):
    """squares: lista (x0, y0, L); ndrones: droni per quadrato; hcols: colonne dell'harvester."""
    regions, specs = [], []
    for (x0, y0, L), nd, hc in zip(squares, ndrones, hcols):
        regions.append([(x0 + i, y0 + j) for i in range(L) for j in range(L)])
        harv = cycle2(x0, y0, hc, L)
        specs.append((harv, True, (x0, y0 + L - 1)))
        for ch in chunks(x0, y0, hc, L, nd - 1):
            specs.append((ch, False, None))
    assert sum(ndrones) == 32, sum(ndrones)
    # il main deve avere indice 0: e' l'harvester del primo quadrato (gia' primo)
    return regions, specs


def build_7x7_22():
    """7x7: harvester 22 (righe 0-3 su colonne 0-3, poi righe 4-6 su colonne 0-1, finisce in (1,6),
    controllo (0,6) a 1 mossa, ritorno a (0,0) come v4); partner 27."""
    regions, specs = [], []
    for k in range(16):
        x0, y0 = 8 * (k % 4), 8 * (k // 4)
        regions.append([(x0 + i, y0 + j) for i in range(7) for j in range(7)])
        h = []
        for j in range(4):
            xs = range(4) if j % 2 == 0 else range(3, -1, -1)
            for i in xs:
                h.append((x0 + i, y0 + j))
        h += [(x0, y0 + 4), (x0 + 1, y0 + 4), (x0 + 1, y0 + 5), (x0, y0 + 5), (x0, y0 + 6), (x0 + 1, y0 + 6)]
        p = [(x0 + 2, y0 + 6), (x0 + 2, y0 + 5), (x0 + 2, y0 + 4), (x0 + 3, y0 + 4), (x0 + 3, y0 + 5), (x0 + 3, y0 + 6)]
        p += [(x0 + 4, y0 + j) for j in range(6, -1, -1)]
        p += [(x0 + 5, y0 + j) for j in range(7)]
        p += [(x0 + 6, y0 + j) for j in range(6, -1, -1)]
        assert len(h) == 22 and len(p) == 27 and len(set(h) | set(p)) == 49
        assert all(dist(a, b) == 1 for a, b in zip(h, h[1:])) and all(dist(a, b) == 1 for a, b in zip(p, p[1:]))
        specs.append((h, False, (x0, y0 + 6)))
        specs.append((p, False, None))
    return regions, specs


def build_7x7_balanced():
    """7x7: harvester 25 celle (righe 0-3 su colonne 0-3 a serpentina, poi righe 4-6 su colonne 0-2,
    finisce in (2,6)), percorso invertito a ogni ciclo (ALT); partner 24 celle."""
    regions, specs = [], []
    for k in range(16):
        x0, y0 = 8 * (k % 4), 8 * (k // 4)
        regions.append([(x0 + i, y0 + j) for i in range(7) for j in range(7)])
        h = []
        for j in range(4):
            xs = range(4) if j % 2 == 0 else range(3, -1, -1)
            for i in xs:
                h.append((x0 + i, y0 + j))
        for j in range(4, 7):
            xs = range(3) if j % 2 == 0 else range(2, -1, -1)
            for i in xs:
                h.append((x0 + i, y0 + j))
        p = [(x0 + 3, y0 + 4), (x0 + 3, y0 + 5), (x0 + 3, y0 + 6)]
        p += [(x0 + 4, y0 + j) for j in range(6, -1, -1)]
        p += [(x0 + 5, y0 + j) for j in range(7)]
        p += [(x0 + 6, y0 + j) for j in range(6, -1, -1)]
        assert len(h) == 25 and len(p) == 24 and len(set(h) | set(p)) == 49
        assert all(dist(a, b) == 1 for a, b in zip(h, h[1:])) and all(dist(a, b) == 1 for a, b in zip(p, p[1:]))
        specs.append((h, False, (x0, y0 + 6)))
        specs.append((p, False, None))
    return regions, specs


LAYOUTS = {
    "7x7 22/27": build_7x7_22,
    "7x7 bilanciato 25/24 ALT": build_7x7_balanced,
    "10x10 4/3 h2/h3": (lambda: build([(11 * (k % 3), 11 * (k // 3), 10) for k in range(9)],
                                      [4, 4, 4, 4, 4, 3, 3, 3, 3], [2, 2, 2, 2, 2, 3, 3, 3, 3])),
    "10x10 4/3 h2/h2": (lambda: build([(11 * (k % 3), 11 * (k // 3), 10) for k in range(9)],
                                      [4, 4, 4, 4, 4, 3, 3, 3, 3], [2] * 9)),
    "10x10 5-4x6-3": (lambda: build([(11 * (k % 3), 11 * (k // 3), 10) for k in range(9)],
                                    [5, 4, 4, 4, 3, 3, 3, 3, 3], [2, 2, 2, 2, 3, 3, 3, 3, 3])),
    "15x15 x4 h2": (lambda: build([(16 * (k % 2), 16 * (k // 2), 15) for k in range(4)], [8] * 4, [2] * 4)),
    "15/16 mix 931 h2": (lambda: build([(0, 0, 15), (16, 0, 15), (0, 16, 15), (16, 16, 16)], [8] * 4, [2] * 4)),
    "7x7 x16 h2 (v4-like)": (lambda: build([(8 * (k % 4), 8 * (k // 4), 7) for k in range(16)], [2] * 16, [2] * 16)),
}


def run(name, P=None, seed=0):
    PP = dict(DEFAULT)
    if P:
        PP.update(P)
    regions, specs = LAYOUTS[name]()
    w = World(seed)
    w.set_regions(regions)
    w.enable_groups()
    w.run(make_main(PP, specs), tmax=1500 * TPS)
    return w


def batch(name, P=None, seeds=range(6), label=""):
    tots, info = [], []
    for s in seeds:
        w = run(name, P, s)
        if not w.done:
            print(name, "seed", s, "NON FINITO", w.pumpkins, w.t / TPS)
            return None
        tots.append(w.harvests[-1][0] / TPS)
        info.append((len(w.harvests), w.fallbacks, w.small_harvests, w.pumpkins / len(w.harvests)))
    m = sum(tots) / len(tots)
    print("%-28s media %6.1f s (%d:%04.1f)  [%s]  raccolti %d fallback %.1f piccoli %.1f resa media %.0f" % (
        label or name, m, m // 60, m % 60, " ".join("%.1f" % t for t in tots),
        sum(i[0] for i in info) / len(info), sum(i[1] for i in info) / len(info),
        sum(i[2] for i in info) / len(info), sum(i[3] for i in info) / len(info)))
    return m


if __name__ == "__main__":
    for name in LAYOUTS:
        batch(name)
