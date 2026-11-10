"""Blocchi indipendenti separati da corridoi vuoti (1 cella): ogni blocco quadrato di lato L >= 6
rende 3072 zucche per cella come il 32x32, e viene raccolto dal suo harvester appena completo,
senza aspettare il resto del campo. L'harvester possiede la colonna sinistra del blocco
(dall'angolo in basso a sinistra (ox,oy) fino a (ox,oy+L-1)): legge measure() dopo aver piantato
(ox,oy) (m0 = numero del gruppo che avra' il quadrato completo) e, finita la sua colonna, controlla
a (ox,oy+L-1) che measure() == m0: vero solo quando il gruppo e' il quadrato completo.
Nel simulatore il test equivale a "tutte le celle della regione mature".

LAYOUT: '15' = 4 blocchi 15x15 (900 celle, 8 droni per blocco: harvester 15 celle + 7 partner
da 2 colonne = 30 celle); '7' = 16 blocchi 7x7 (784 celle, 2 droni: harvester 3 colonne = 21 celle
in serpentina, partner 4 colonne = 28 celle in ciclo).
"""
import sys
from pumpsim import *
import pump_blk
from pump_blk import goto, block_cycle, dist

DEFAULT = dict(pump_blk.DEFAULT)
DEFAULT.update(LAYOUT="7", GROUPS=True, T_MAX=6.0, P_FALLBACK=20.0,
               WLOW=0.25, WTGT=0.5, FERT_T=0.0, FERT_K=32, FERT_GEN=4)


def layout(kind):
    """Ritorna (regioni, droni): regioni = liste di celle per blocco; droni = lista di
    (cells, cyclic, harvester_check_cell or None) in ordine di spawn (drone 0 = main)."""
    regions, drones = [], []
    if kind == "15":
        L, pitch, nb = 15, 16, 2
    elif kind == "7":
        L, pitch, nb = 7, 8, 4
    elif kind == "9":
        L, pitch, nb = 9, 10, 3
    else:
        raise ValueError(kind)
    for bj in range(nb):
        for bi in range(nb):
            ox, oy = bi * pitch, bj * pitch
            regions.append([(ox + i, oy + j) for i in range(L) for j in range(L)])
            if kind == "15":
                harv = [(ox, oy + j) for j in range(L)]
                drones.append((harv, False, (ox, oy + L - 1)))
                for k in range(7):
                    x0 = ox + 1 + 2 * k
                    cells = [(x0, oy + j) for j in range(L)] + [(x0 + 1, oy + j) for j in range(L - 1, -1, -1)]
                    drones.append((cells, True, None))
            elif kind == "7":
                # harvester: colonne 0-2 in serpentina per righe da (ox,oy) a (ox,oy+6)
                harv = []
                for j in range(L):
                    xs = range(3) if j % 2 == 0 else range(2, -1, -1)
                    for i in xs:
                        harv.append((ox + i, oy + j))
                assert harv[0] == (ox, oy)
                drones.append((harv, False, (ox, oy + L - 1)))
                # partner: colonne 3-6 (4x7), ciclo hamiltoniano
                x0 = ox + 3
                cells = [(x0 + i, oy) for i in range(4)]
                for i in range(3, -1, -1):
                    ys = range(1, L) if (3 - i) % 2 == 0 else range(L - 1, 0, -1)
                    for j in ys:
                        cells.append((x0 + i, oy + j))
                assert all(dist(a, b) == 1 for a, b in zip(cells, cells[1:])) and dist(cells[0], cells[-1]) == 1
                drones.append((cells, True, None))
            elif kind == "9":
                # 9 blocchi, 32 droni: 5 blocchi con 4 droni, 4 con 3
                harv = [(ox, oy + j) for j in range(L)]
                drones.append((harv, False, (ox, oy + L - 1)))
                b = bj * nb + bi
                nparts = 3 if b < 5 else 2
                rest = [(ox + 1 + i, oy + j) for i in range(8) for j in range(L)]
                # partner a strisce di colonne: 8 colonne / nparts
                per = [8 // nparts + (1 if i < 8 % nparts else 0) for i in range(nparts)]
                x0 = ox + 1
                for w in per:
                    cells = []
                    for i in range(w):
                        ys = range(L) if i % 2 == 0 else range(L - 1, -1, -1)
                        for j in ys:
                            cells.append((x0 + i, oy + j))
                    x0 += w
                    drones.append((cells, False, None))
    # il main deve essere il primo: e' l'harvester del blocco 0 (contiene (0,0))
    return regions, drones


def drone_prog(spec, P, is_main=False):
    cells, cyclic, check = spec
    alt = (not cyclic) and check is not None and P.get("ALT", False)
    if alt:
        x0, y0 = cells[0]
        L = check[1] - y0 + 1
        checks = [(x0, y0 + L - 1), (x0 + L - 1, y0)]
        cells = list(cells)

    def prog(d):
        yield goto(d, cells[0][0], cells[0][1])
        first = True
        gens = [0] * len(cells)
        pos = 0
        cyc = 0
        m0 = [None]
        chk = check
        while True:
            if alt:
                m0 = [m0[0], cells.index((x0, y0))]
            elif chk is not None:
                m0 = [m0[0], 0]
            if not cyclic and (d.x, d.y) != cells[0]:
                yield goto(d, cells[0][0], cells[0][1])
            pos = yield from block_cycle(d, P, cells, first, gens, pos, cyclic, None, m0 if chk else None)
            first = False
            if alt:
                cells.reverse()
                gens.reverse()
                pos = len(cells) - 1 - pos
                chk = min(checks, key=lambda c: dist((d.x, d.y), c))
            if chk is not None:
                if d.get_entity_type() == NONE:
                    yield 3
                    continue
                t_fill = d.w.t
                if (d.x, d.y) != chk:
                    yield goto(d, chk[0], chk[1])
                if P["GROUPS"]:
                    # while measure() != m0 and tempo < T_MAX: pass
                    ok = yield from d.wait_measure(m0[0], 3, P["T_MAX"] * TPS)
                    yield 3
                    if not ok:
                        d.w.fallbacks += 1
                        if not d.can_harvest():
                            continue
                else:
                    yield from d.wait_region(3)
                t_ok = d.w.t
                before = d.w.pumpkins
                yield 3 + d.harvest()
                cyc += 1
                if is_main:
                    d.w.log.append((cyc, t_fill / TPS, t_ok / TPS, d.w.pumpkins - before, d.w.tank()))
                yield 6
                if d.w.done:
                    return
            else:
                t0 = d.w.t
                while d.get_entity_type() != NONE:
                    if P["P_FALLBACK"] > 0 and d.w.t - t0 >= P["P_FALLBACK"] * TPS:
                        if d.can_harvest():
                            d.w.fallbacks += 1
                            yield 2 + d.harvest()
                        break
                    d.cell().watchers.append((d, 3, d.w.t, d.wait_id))
                    if P["P_FALLBACK"] > 0:
                        d.w.wake_at(d, t0 + P["P_FALLBACK"] * TPS, d.wait_id)
                    yield None
                yield 3
                if not cyclic:
                    cells.reverse()
                    gens.reverse()
    return prog


def spawn_range(lo, hi, specs, P):
    def prog(d):
        a, b = lo, hi
        while b - a > 1:
            mid = (a + b) // 2
            yield 4 + d.spawn(spawn_range(mid, b, specs, P))
            b = mid
        yield from drone_prog(specs[a], P)(d)
    return prog


def make_main(P, specs):
    def main_prog(d):
        yield ACT  # clear()
        yield 2 + d.spawn(spawn_range(1, len(specs), specs, P))
        yield from drone_prog(specs[0], P, is_main=True)(d)
    return main_prog


def run(P=None, seed=0, dev=0.2):
    PP = dict(DEFAULT)
    if P:
        PP.update(P)
    regions, specs = layout(PP["LAYOUT"])
    assert len(specs) == 32, len(specs)
    w = World(seed, dev=dev)
    w.set_regions(regions)
    if PP["GROUPS"]:
        w.enable_groups()
    w.run(make_main(PP, specs), tmax=1500 * TPS)
    return w


def batch(P=None, seeds=range(4), label="", dev=0.2):
    tots, info = [], []
    for s in seeds:
        w = run(P, s, dev)
        if not w.done:
            print(label, "seed", s, "NON FINITO", w.pumpkins, w.t / TPS)
            return None
        tots.append(w.harvests[-1][0] / TPS)
        info.append((len(w.harvests), w.fallbacks, w.small_harvests, w.pumpkins / len(w.harvests)))
    m = sum(tots) / len(tots)
    print("%-36s media %6.1f s (%d:%04.1f)  [%s]  raccolti %d fallback %.1f piccoli %.1f resa media %.0f" % (
        label or str(P), m, m // 60, m % 60, " ".join("%.1f" % t for t in tots),
        sum(i[0] for i in info) / len(info), sum(i[1] for i in info) / len(info),
        sum(i[2] for i in info) / len(info), sum(i[3] for i in info) / len(info)))
    return m


if __name__ == "__main__":
    seeds = range(6)
    batch({}, seeds, label="v4 7x7 corridoi, gruppi reali, m0")
    batch({"GROUPS": False}, seeds, label="v4 7x7 (regioni)")
    batch({"CHECK_END": True}, seeds, label="(idem)")
