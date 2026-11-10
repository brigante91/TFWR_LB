"""Strategia a blocchi: ogni drone possiede 32 celle (colonna 1x32, serpentina 2x16, 4x8, 8x4);
riempimento in ordine di serpentina (invertito a ogni ciclo, cosi' non c'e' viaggio di ritorno),
poi passate sulle celle pendenti con spostamenti brevi (goto con wrap). Barriera del main come v2:
il main ha un blocco che contiene x = 0 e, finito il suo blocco, si porta su una cella x = 0.

Parametri in piu' rispetto a pump_v3: SHAPE ('col', '2x16', '4x8', '8x4'), ORDER ('snake', 'nn').
"""
import sys
from pumpsim import *
import pump_v3
from pump_v3 import water_up

DEFAULT = dict(pump_v3.DEFAULT)
DEFAULT.update(SHAPE="4x8", ORDER="snake", MAIN_COL=False, WAIT_FERT=0, PLANT_ORDER="snake",
               HELP=False, HELP_W=1.0, SCAN2=False, MARGIN=1.0, IDLE_SCAN=False)


def blocks(shape, main_col=False):
    """Lista di 32 blocchi; ogni blocco e' una lista di celle (x, y) che forma un CICLO
    hamiltoniano (celle consecutive adiacenti, ultima adiacente alla prima): il riempimento puo'
    partire da qualunque cella e tornare al punto di partenza. Il blocco 0 contiene x = 0."""
    out = []
    if shape == "col":
        for x in range(S):
            out.append([(x, y) for y in range(S)])
        return out
    bw, bh = {"2x16": (2, 16), "4x8": (4, 8), "8x4": (8, 4), "16x2": (16, 2)}[shape]
    for by in range(S // bh):
        for bx in range(S // bw):
            x0, y0 = bx * bw, by * bh
            cells = [(x0, y0 + j) for j in range(bh)]
            for j in range(bh - 1, -1, -1):
                xs = range(1, bw) if (bh - 1 - j) % 2 == 0 else range(bw - 1, 0, -1)
                for i in xs:
                    cells.append((x0 + i, y0 + j))
            assert len(cells) == bw * bh and dist(cells[0], cells[-1]) == 1
            assert all(dist(a, b) == 1 for a, b in zip(cells, cells[1:]))
            out.append(cells)
    return out


def dist(a, b):
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return min(dx, S - dx) + min(dy, S - dy)


def goto(d, tx, ty):
    """Spostamento con wrap sul percorso piu' corto. Costo codice ~8 + 1 per mossa."""
    cost = 8
    dx = (tx - d.x) % S
    if dx <= S // 2:
        for _ in range(dx):
            cost += 1 + d.move(E)
    else:
        for _ in range(S - dx):
            cost += 1 + d.move(W)
    dy = (ty - d.y) % S
    if dy <= S // 2:
        for _ in range(dy):
            cost += 1 + d.move(N)
    else:
        for _ in range(S - dy):
            cost += 1 + d.move(So)
    return cost


def block_cycle(d, P, cells, first, gens, pos, cyclic=True, stops=None, m0ref=None):
    """Riempimento del blocco partendo da cells[pos] lungo il ciclo e passate sulle pendenti.
    Ritorna (nuova posizione) quando tutte le celle sono mature o il main ha raccolto."""
    t0 = d.w.t
    pending = []
    ready_by = [0.0] * len(cells)
    yield 2
    n = len(cells)
    if not cyclic:
        pos = 0
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
            if m0ref is not None and k == (m0ref[1] if len(m0ref) > 1 else 0):
                m0ref[0] = d.measure()
                c += 2
            if d.get_water() < P["WLOW"] and d.num_water() >= P["RES"]:
                c += water_up(d, P["WTGT"])
            pending.append(k)
            c += 1
            if P["SCAN2"]:
                # stima del tempo entro cui la cella e' matura (o morta): 2.4 s / (1 + 4 acqua)
                c += 3
                ready_by[k] = d.w.t + P["MARGIN"] * 1.2 * GROW / (1.0 + 4.0 * d.get_water())
        else:
            c += 2
            if not d.can_harvest():
                pending.append(k)
                c += 1
        nk = (k + 1) % n
        if cyclic or nk != 0:
            c += goto(d, cells[nk][0], cells[nk][1])
        yield c
    yield 2
    if P["SCAN2"] and stops:
        # passata 2 a scansione: fermate con controllo di se' e dei vicini W/E (get_entity_type(dir))
        idx = {cc: i for i, cc in enumerate(cells)}
        replanted = []
        seen_t = {}
        for (sx, sy) in stops:
            c = 4 + goto(d, sx, sy)
            found = []
            t = d.get_entity_type()
            c += 3
            if t == NONE:
                yield c
                return idx[(d.x, d.y)]
            if t == DEAD:
                found.append((d.x, d.y))
            seen_t[(d.x, d.y)] = d.w.t
            for dx, dy in ((1, 0), (-1, 0)):
                nx, ny = (d.x + dx) % S, (d.y + dy) % S
                c += 3
                if (nx, ny) in idx:
                    seen_t[(nx, ny)] = d.w.t
                if d.w.cells[nx][ny].ent == DEAD:
                    found.append((nx, ny))
            yield c
            for (x, y) in found:
                c = goto(d, x, y) + 3
                if d.get_entity_type() != DEAD:
                    yield c
                    continue
                k = idx.get((x, y))
                c += d.harvest() + d.plant() + 3
                if k is not None:
                    gens[k] += 1
                    replanted.append(k)
                if P["WREP"] > 0 and d.num_water() >= P["RESREP"]:
                    c += 3 + water_up(d, P["WREP"])
                yield c
        # pendenti: ripiantate + celle che potevano essere ancora in crescita quando viste
        pending = [k for k in pending if ready_by[k] > seen_t.get(cells[k], d.w.t) or k in replanted]
        pos = idx[(d.x, d.y)]
        pending.sort(key=lambda k: (k - pos) % n)
        yield 10
    while len(pending) > 0:
        left = []
        yield 2
        order = pending
        if P["ORDER"] == "nn":
            order = []
            rest = list(pending)
            cur = (d.x, d.y)
            while rest:
                best = min(rest, key=lambda k: dist(cur, cells[k]))
                rest.remove(best)
                order.append(best)
                cur = cells[best]
            yield 4 * len(pending)
        for k in order:
            c = 3 + goto(d, cells[k][0], cells[k][1])
            pos = k
            c += 3
            while True:
                t = d.get_entity_type()
                c += 3
                if t == RIPE:
                    yield c
                    break
                if t == NONE:
                    yield c
                    return pos
                late = (d.w.t - t0) / TPS > P["FERT_T"] and len(pending) <= P["FERT_K"]
                if t == DEAD:
                    gens[k] += 1
                    c += d.harvest() + d.plant() + 3
                    if m0ref is not None and k == (m0ref[1] if len(m0ref) > 1 else 0):
                        m0ref[0] = d.measure()
                        c += 2
                    if late and gens[k] >= P["FERT_GEN"] and d.num_fert() >= 1:
                        c += 2 + d.fertilize(1)
                        yield c
                        c = 0
                        continue
                    if P["WREP"] > 0 and (P["WREP_K"] == 0 or len(pending) <= P["WREP_K"]) and d.num_water() >= P["RESREP"]:
                        c += 3 + water_up(d, P["WREP"])
                    if len(pending) > P["WAIT_K"]:
                        left.append(k)
                        yield c + 1
                        break
                    yield c
                    c = 0
                    continue
                if late and gens[k] >= P["FERT_GEN"] and d.num_fert() >= 1:
                    c += 2 + d.fertilize(1)
                    yield c
                    c = 0
                    continue
                if len(pending) > P["WAIT_K"]:
                    left.append(k)
                    yield c + 1
                    break
                yield c
                c = 0
                yield from d.wait_cell(7, GROWING)
        pending = left
        yield 2
    return pos


def scan_stops(cells):
    """Percorso di scansione di un blocco 4x8 (o 8x4): fermate sulle due colonne (righe) centrali,
    ogni fermata vede se stessa e i 4 vicini -> tutte le celle del blocco sono viste in un giro."""
    xs = sorted(set(x for x, y in cells))
    ys = sorted(set(y for x, y in cells))
    if len(xs) == 4:
        up = [(xs[1], y) for y in ys]
        down = [(xs[2], y) for y in reversed(ys)]
        return up + down
    if len(ys) == 4:
        right = [(x, ys[1]) for x in xs]
        left = [(x, ys[2]) for x in reversed(xs)]
        return right + left
    return list(cells)


def help_scan(d, P, partner):
    """Il drone ha finito il suo blocco: fa giri di scansione sul blocco del partner, raccoglie e
    ripianta le morte che vede (anche nei vicini, con get_entity_type(dir)), finche' la cella sotto
    di lui diventa None (raccolto del main). Ritorna allora."""
    pset = set(partner)
    stops = scan_stops(partner)
    i = 0
    while True:
        sx, sy = stops[i % len(stops)]
        i += 1
        c = 3 + goto(d, sx, sy)
        while True:
            # guarda se stesso e i vicini nel blocco del partner
            t = d.get_entity_type()
            c += 2
            if t == NONE:
                yield c
                return
            dead = []
            if t == DEAD:
                dead.append((d.x, d.y))
            for dx, dy in DIRS:
                nx, ny = (d.x + dx) % S, (d.y + dy) % S
                if (nx, ny) in pset:
                    c += 3
                    if d.w.cells[nx][ny].ent == DEAD:
                        dead.append((nx, ny))
            if not dead:
                yield c
                break
            x, y = dead[0]
            c += goto(d, x, y)
            if d.get_entity_type() == DEAD:
                c += 2 + d.harvest() + d.plant()
                if P["HELP_W"] > 0 and d.num_water() >= P["RESREP"]:
                    c += 3 + water_up(d, P["HELP_W"])
            yield c
            c = 0


def worker(cells, P, is_main=False, partner=None):
    stops = scan_stops(cells)

    def prog(d):
        yield goto(d, cells[0][0], cells[0][1])
        first = True
        gens = [0] * len(cells)
        pos = 0
        cyc = 0
        while True:
            pos = yield from block_cycle(d, P, cells, first, gens, pos, True, stops)
            first = False
            if is_main:
                t_fill = d.w.t
                if d.x != 0:
                    # si porta su una cella x=0 del blocco (stessa riga)
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
                if P["IDLE_SCAN"] and d.get_entity_type() != NONE:
                    yield 2
                    yield from help_scan(d, P, cells)
                    k = min(range(len(cells)), key=lambda k: dist((d.x, d.y), cells[k]))
                    yield goto(d, cells[k][0], cells[k][1])
                    pos = k
                if P["HELP"] and partner is not None and d.get_entity_type() != NONE:
                    yield 2
                    yield from help_scan(d, P, partner)
                    # torna alla cella piu' vicina del proprio blocco e riparte da li'
                    k = min(range(len(cells)), key=lambda k: dist((d.x, d.y), cells[k]))
                    yield goto(d, cells[k][0], cells[k][1])
                    pos = k
                while d.get_entity_type() != NONE:
                    yield from d.wait_cell(3, d.get_entity_type())
                yield 3
    return prog


def spawn_range(lo, hi, blks, P):
    def prog(d):
        a, b = lo, hi
        while b - a > 1:
            mid = (a + b) // 2
            yield 4 + d.spawn(spawn_range(mid, b, blks, P))
            b = mid
        partner = blks[a ^ 1] if (a ^ 1) != 0 else None
        yield from worker(blks[a], P, partner=partner)(d)
    return prog


def make_main(P):
    blks = blocks(P["SHAPE"])

    def main_prog(d):
        yield ACT  # clear()
        yield 2 + d.spawn(spawn_range(1, S, blks, P))
        yield from worker(blks[0], P, is_main=True)(d)
    return main_prog


def run(P=None, seed=0, dev=0.2):
    PP = dict(DEFAULT)
    if P:
        PP.update(P)
    w = World(seed, dev=dev)
    w.run(make_main(PP))
    return w


def batch(P=None, seeds=range(4), label="", dev=0.2):
    tots = []
    for s in seeds:
        w = run(P, s, dev)
        if not w.harvests:
            print(label, "seed", s, "BLOCCATO")
            return None
        tots.append(w.harvests[-1][0] / TPS)
    m = sum(tots) / len(tots)
    print("%-44s media %6.1f s (%d:%04.1f)  [%s]" % (label or str(P), m, m // 60, m % 60,
                                                   " ".join("%.1f" % t for t in tots)))
    return m


if __name__ == "__main__":
    for shape in ("col", "2x16", "4x8", "8x4"):
        batch({"SHAPE": shape, "WLOW": 0.25, "WTGT": 0.5}, label="SHAPE %s snake" % shape)
        batch({"SHAPE": shape, "WLOW": 0.25, "WTGT": 0.5, "ORDER": "nn"}, label="SHAPE %s nn" % shape)
