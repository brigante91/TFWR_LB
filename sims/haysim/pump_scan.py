"""Strategia 'scan': ogni drone riempie il suo blocco (ciclo hamiltoniano), poi fa giri di
scansione su un percorso corto (fermate sulle colonne centrali del blocco) guardando la cella sotto
di se' e le 4 vicine con get_entity_type(dir): trova le zucche morte senza visitare ogni cella,
le raccoglie e ripianta (acqua / fertilizzante), e continua finche' la cella sotto di lui e' None
(il main ha raccolto). I worker non hanno bisogno di sapere quali celle sono mature: la barriera e'
solo del main (measure()==measure(West) a x=0, controllata a ogni fermata del suo giro su x=0).

Layout: main = blocco 2x16 (colonne 0-1, righe 0-15), giro su x=0; un worker 2x16 sotto (righe 16-31);
28 worker 4x8 sulle colonne 2-29; 2 worker 2x16 sulle colonne 30-31.

Parametri: WLOW/WTGT/RES (acqua fresche), WREP/RESREP (acqua ripiantate), WAIT_K (aspetta sul posto
dopo una ripiantata se nel giro ha trovato <= WAIT_K morte), FERT_GEN (fertilizzante dalla
FERT_GEN-esima morte della cella nel ciclo), MAIN_WAIT (anche il main aspetta sul posto se a x=0).
"""
import sys
from pumpsim import *
from pump_v3 import water_up
from pump_blk import goto, dist

DEFAULT = dict(WLOW=0.25, WTGT=0.5, RES=0, WREP=1.0, RESREP=0, WAIT_K=2, FERT_GEN=3,
               MAIN_WAIT=False, CHECK_NEIGH=True, FERT_T=0.0, WMIN_WAIT=0.4)


def cycle_cells(x0, y0, bw, bh):
    """Ciclo hamiltoniano su un blocco bw x bh (bh pari): colonna 0 in su, poi righe a serpentina
    sulle colonne 1..bw-1 scendendo."""
    cells = [(x0, y0 + j) for j in range(bh)]
    for j in range(bh - 1, -1, -1):
        xs = range(1, bw) if (bh - 1 - j) % 2 == 0 else range(bw - 1, 0, -1)
        for i in xs:
            cells.append((x0 + i, y0 + j))
    assert all(dist(a, b) == 1 for a, b in zip(cells, cells[1:])) and dist(cells[0], cells[-1]) == 1
    return cells


def layout():
    specs = []  # (cells, stops, is_main)
    # main: colonne 0-1 righe 0-15, fermate su x=0 (su e giu')
    cells = cycle_cells(0, 0, 2, 16)
    stops = [(0, y) for y in range(16)] + [(0, y) for y in range(14, 0, -1)]
    specs.append((cells, stops))
    cells = cycle_cells(0, 16, 2, 16)
    stops = [(0, y) for y in range(16, 32)] + [(0, y) for y in range(30, 16, -1)]
    specs.append((cells, stops))
    for bx in range(7):
        for by in range(4):
            x0, y0 = 2 + 4 * bx, 8 * by
            cells = cycle_cells(x0, y0, 4, 8)
            stops = [(x0 + 1, y0 + j) for j in range(8)] + [(x0 + 2, y0 + j) for j in range(7, -1, -1)]
            specs.append((cells, stops))
    for by in range(2):
        cells = cycle_cells(30, 16 * by, 2, 16)
        stops = [(30, 16 * by + j) for j in range(16)] + [(30, 16 * by + j) for j in range(14, 0, -1)]
        specs.append((cells, stops))
    assert len(specs) == 32
    allc = set()
    for c, s in specs:
        allc |= set(c)
    assert len(allc) == 1024
    return specs


def fill(d, P, cells, first, gens, pos):
    n = len(cells)
    yield 2
    for i in range(n):
        k = (pos + i) % n
        c = 3
        if first:
            c += 2
            if not d.cell().soil:
                c += d.till()
        t = d.get_entity_type()
        c += 3
        if t == DEAD:
            c += d.harvest()
            t = NONE
        c += 2
        if t == NONE:
            gens[k] = 0
            c += d.plant() + 2
            if d.get_water() < P["WLOW"] and d.num_water() >= P["RES"]:
                c += water_up(d, P["WTGT"])
        nk = (k + 1) % n
        c += goto(d, cells[nk][0], cells[nk][1])
        yield c


def replant(d, P, gens, k, t0):
    """Sulla cella morta: harvest, plant, fertilizzante o acqua. Ritorna i tick."""
    gens[k] += 1
    c = d.harvest() + d.plant() + 4
    if gens[k] >= P["FERT_GEN"] and (d.w.t - t0) / TPS >= P["FERT_T"] and d.num_fert() >= 1:
        c += d.fertilize(1)
    elif P["WREP"] > 0 and d.num_water() >= P["RESREP"]:
        c += 2 + water_up(d, P["WREP"])
    return c


def scan_loop(d, P, cells, stops, gens, is_main, t0):
    """Giri di scansione finche' la cella sotto il drone e' None. Ritorna l'indice (in cells)
    della cella dove si trova."""
    idx = {c: i for i, c in enumerate(cells)}
    si = min(range(len(stops)), key=lambda i: dist((d.x, d.y), stops[i]))
    nstops = len(stops)
    lap = 0
    ndead_prev = 99
    ndead_cur = 0
    while True:
        if si % nstops == 0:
            lap += 1
            ndead_prev = ndead_cur
            ndead_cur = 0
        sx, sy = stops[si % nstops]
        si += 1
        c = 4 + goto(d, sx, sy)
        if is_main:
            # barriera: while measure() != measure(West)
            c += 3
            if d.complete():
                yield c
                return idx[(d.x, d.y)]
        found = []
        t = d.get_entity_type()
        c += 3
        if t == NONE:
            yield c
            return idx[(d.x, d.y)]
        if t == DEAD:
            found.append((d.x, d.y))
        if P["CHECK_NEIGH"]:
            for dx, dy in DIRS:
                nx, ny = (d.x + dx) % S, (d.y + dy) % S
                c += 3
                if d.w.cells[nx][ny].ent == DEAD:
                    found.append((nx, ny))
        yield c
        for (x, y) in found:
            c = goto(d, x, y) + 3
            if d.get_entity_type() != DEAD:
                yield c
                continue
            k = idx.get((x, y))
            if k is None:
                # cella di un vicino: la sistemo comunque (senza contare le generazioni)
                tmp = [0]
                c += replant(d, P, tmp, 0, t0)
                yield c
                continue
            c += replant(d, P, gens, k, t0)
            ndead_cur += 1
            yield c
            # attesa sul posto se poche morte in questo giro e nel precedente, e cella bagnata
            if (lap >= 2 and ndead_prev + ndead_cur <= P["WAIT_K"] and d.get_water() >= P["WMIN_WAIT"]
                    and (not is_main or (P["MAIN_WAIT"] and d.x == 0))):
                while True:
                    t = d.get_entity_type()
                    if t == RIPE:
                        yield 4
                        break
                    if t == NONE:
                        yield 4
                        return k
                    if t == DEAD:
                        yield 4 + replant(d, P, gens, k, t0)
                        ndead_cur += 1
                        continue
                    yield from d.wait_cell(7, GROWING)


def drone_prog(cells, stops, P, is_main):
    def prog(d):
        yield goto(d, cells[0][0], cells[0][1])
        first = True
        gens = [0] * len(cells)
        pos = 0
        cyc = 0
        while True:
            t0 = d.w.t
            yield from fill(d, P, cells, first, gens, pos)
            first = False
            t_fill = d.w.t
            pos = yield from scan_loop(d, P, cells, stops, gens, is_main, t0)
            if is_main:
                if d.x != 0:
                    yield goto(d, 0, d.y)
                    pos = cells.index((0, d.y))
                yield from d.wait_complete(3)
                t_ok = d.w.t
                before = d.w.pumpkins
                yield 3 + d.harvest()
                cyc += 1
                d.w.log.append((cyc, t_fill / TPS, t_ok / TPS, d.w.pumpkins - before, d.w.tank()))
                yield 6
                if d.w.done:
                    return
            else:
                while d.get_entity_type() != NONE:
                    yield from d.wait_cell(3, d.get_entity_type())
                yield 3
    return prog


def spawn_range(lo, hi, specs, P):
    def prog(d):
        a, b = lo, hi
        while b - a > 1:
            mid = (a + b) // 2
            yield 4 + d.spawn(spawn_range(mid, b, specs, P))
            b = mid
        yield from drone_prog(specs[a][0], specs[a][1], P, False)(d)
    return prog


def make_main(P, specs):
    def main_prog(d):
        yield ACT
        yield 2 + d.spawn(spawn_range(1, 32, specs, P))
        yield from drone_prog(specs[0][0], specs[0][1], P, True)(d)
    return main_prog


def run(P=None, seed=0, dev=0.2):
    PP = dict(DEFAULT)
    if P:
        PP.update(P)
    w = World(seed, dev=dev)
    w.run(make_main(PP, layout()))
    return w


def batch(P=None, seeds=range(4), label="", dev=0.2):
    tots = []
    for s in seeds:
        w = run(P, s, dev)
        if not w.done:
            print(label, "seed", s, "NON FINITO", w.pumpkins, w.t / TPS)
            return None
        tots.append(w.harvests[-1][0] / TPS)
    m = sum(tots) / len(tots)
    print("%-44s media %6.1f s (%d:%04.1f)  [%s]" % (label or str(P), m, m // 60, m % 60,
                                                   " ".join("%.1f" % t for t in tots)))
    return m


if __name__ == "__main__":
    batch({}, label="scan default")
    batch({"WAIT_K": 0}, label="scan WAIT_K0")
    batch({"WAIT_K": 1}, label="scan WAIT_K1")
    batch({"WAIT_K": 3}, label="scan WAIT_K3")
    batch({"WMIN_WAIT": 0.6}, label="scan WMIN_WAIT .6")
    batch({"FERT_GEN": 2}, label="scan FERT_GEN2")
    batch({"FERT_GEN": 4}, label="scan FERT_GEN4")
    batch({"FERT_GEN": 99}, label="scan no fert")
    batch({"MAIN_WAIT": True}, label="scan MAIN_WAIT")
