"""v4: 16 quadrati 8x8 ADIACENTI (origine (8*(k%4), 8*(k//4))), 2 droni per quadrato, ognuno con
un blocco 4x8 (meta' sinistra = harvester, meta' destra = partner) con la logica di v3
(ciclo hamiltoniano, pending list, acqua, fertilizzante). Raccolto per quadrato appena completo:
l'harvester legge m0 = measure() su (x0,y0) appena piantata e, finito il suo blocco, aspetta su
CHECK ((3,7) o (7,7) del quadrato) che measure() == m0; se aspetta piu' di T_MAX raccoglie
comunque il gruppo su cui sta (rete di sicurezza). Il simulatore usa la fusione reale dei gruppi.
"""
import sys
from pumpsim import *
import pump_blk
from pump_blk import goto, block_cycle, dist
from pump_scan import cycle_cells

DEFAULT = dict(pump_blk.DEFAULT)
DEFAULT.update(WLOW=0.25, WTGT=0.5, FERT_T=0.0, FERT_K=32, FERT_GEN=4,
               CHECK="37", T_MAX=6.0, P_FALLBACK=0.0, MODE="m0", PAIR_D=5, FALL_MIN=0)


def layout():
    specs = []   # (cells, is_harv, check)
    for k in range(16):
        x0, y0 = 8 * (k % 4), 8 * (k // 4)
        left = cycle_cells(x0, y0, 4, 8)
        right = cycle_cells(x0 + 4, y0, 4, 8)
        specs.append((left, True, (x0 + 3, y0 + 7), (x0 + 7, y0 + 7)))
        specs.append((right, False, None, None))
    return specs


def harvester(cells, check, P, is_main):
    def prog(d):
        yield goto(d, cells[0][0], cells[0][1])
        first = True
        gens = [0] * len(cells)
        pos = 0
        m0 = [None]
        cyc = 0
        while True:
            pos = yield from block_cycle(d, P, cells, first, gens, pos, True, None, m0)
            first = False
            if d.get_entity_type() == NONE:
                yield 3
                continue        # qualcuno ha raccolto durante le passate: si riparte
            if (d.x, d.y) != check:
                yield goto(d, check[0], check[1])
            t_wait = d.w.t
            ok = yield from d.wait_measure(m0[0], 3, P["T_MAX"] * TPS)
            yield 4
            if not ok:
                d.w.fallbacks += 1
                if not d.can_harvest():
                    # la cella del partner non e' matura: riprova dall'inizio
                    pos = cells.index((d.x, d.y)) if (d.x, d.y) in cells else pos
                    if (d.x, d.y) not in cells:
                        yield goto(d, cells[pos][0], cells[pos][1])
                    continue
            before = d.w.pumpkins
            yield 1 + d.harvest()
            cyc += 1
            if is_main:
                d.w.log.append((cyc, d.w.t / TPS, d.w.pumpkins - before, d.w.tank()))
                yield 8
                if d.w.done:
                    return
            if (d.x, d.y) in cells:
                pos = cells.index((d.x, d.y))
            else:
                yield goto(d, cells[pos][0], cells[pos][1])
    return prog


def pair_checker(cells, P, is_main):
    """Test 'gruppo di lato >= PAIR_D+1': measure() su A e su B (stessa colonna, distanza PAIR_D)
    uguali <=> stesso quadrato <=> lato >= PAIR_D+1 >= 6 -> resa piena per cella. Si alterna A/B.
    Dopo T_MAX senza successo raccoglie comunque il gruppo in cui sta (sblocco)."""
    x0, y0 = cells[0]
    A = (x0 + 3, y0 + 7)
    B = (x0 + 3, y0 + 7 - P["PAIR_D"])

    def prog(d):
        yield goto(d, cells[0][0], cells[0][1])
        first = True
        gens = [0] * len(cells)
        pos = 0
        cyc = 0
        while True:
            pos = yield from block_cycle(d, P, cells, first, gens, pos)
            first = False
            if d.get_entity_type() == NONE:
                yield 3
                continue
            t_wait = d.w.t
            cur, other = A, B
            if (d.x, d.y) != cur:
                yield goto(d, cur[0], cur[1])
            harvested = False
            while True:
                m = d.measure()
                yield 2 + goto(d, other[0], other[1])
                cur, other = other, cur
                t = d.get_entity_type()
                if t == NONE:
                    break
                if t == RIPE and m is not None and d.measure() == m:
                    before = d.w.pumpkins
                    yield 3 + d.harvest()
                    harvested = True
                    break
                if d.w.t - t_wait > P["T_MAX"] * TPS:
                    if t == RIPE and (P["FALL_MIN"] == 0 or d.cell().grp[2] >= P["FALL_MIN"]):
                        d.w.fallbacks += 1
                        before = d.w.pumpkins
                        yield 3 + d.harvest()
                        harvested = True
                    break
                yield 3
            if harvested and is_main:
                cyc += 1
                d.w.log.append((cyc, d.w.t / TPS, d.w.pumpkins - before, d.w.tank()))
                yield 8
                if d.w.done:
                    return
            pos = cells.index((d.x, d.y))
    return prog


def partner(cells, P):
    def prog(d):
        yield goto(d, cells[0][0], cells[0][1])
        first = True
        gens = [0] * len(cells)
        pos = 0
        while True:
            pos = yield from block_cycle(d, P, cells, first, gens, pos)
            first = False
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
    return prog


def make_prog(spec, P, is_main=False):
    cells, is_h, c37, c77 = spec
    if P["MODE"] == "pair":
        return pair_checker(cells, P, is_main)
    if is_h:
        return harvester(cells, c37 if P["CHECK"] == "37" else c77, P, is_main)
    return partner(cells, P)


def spawn_range(lo, hi, specs, P):
    def prog(d):
        a, b = lo, hi
        while b - a > 1:
            mid = (a + b) // 2
            yield 4 + d.spawn(spawn_range(mid, b, specs, P))
            b = mid
        yield from make_prog(specs[a], P)(d)
    return prog


def make_main(P, specs):
    def main_prog(d):
        yield ACT
        yield 2 + d.spawn(spawn_range(1, 32, specs, P))
        yield from make_prog(specs[0], P, True)(d)
    return main_prog


def run(P=None, seed=0, dev=0.2):
    PP = dict(DEFAULT)
    if P:
        PP.update(P)
    w = World(seed, dev=dev)
    w.enable_groups()
    w.run(make_main(PP, layout()), tmax=1500 * TPS)
    return w


def batch(P=None, seeds=range(4), label=""):
    tots, info = [], []
    for s in seeds:
        w = run(P, s)
        if not w.done:
            print(label, "seed", s, "NON FINITO: zucche", w.pumpkins, "t", w.t / TPS, "raccolti", len(w.harvests))
            return None
        tots.append(w.harvests[-1][0] / TPS)
        ys = [y for _, y in w.harvests]
        info.append((len(ys), w.fallbacks, w.small_harvests, sum(ys) / len(ys)))
    m = sum(tots) / len(tots)
    print("%-36s media %6.1f s (%d:%04.1f) [%s]  raccolti %d  fallback %.1f  piccoli %.1f  resa media %.0f" % (
        label or str(P), m, m // 60, m % 60, " ".join("%.1f" % t for t in tots),
        sum(i[0] for i in info) / len(info), sum(i[1] for i in info) / len(info),
        sum(i[2] for i in info) / len(info), sum(i[3] for i in info) / len(info)))
    return m


if __name__ == "__main__":
    batch({"MODE": "pair"}, label="v4 pair T6")
    batch({"MODE": "pair", "T_MAX": 3.0}, label="v4 pair T3")
    batch({"MODE": "pair", "T_MAX": 12.0}, label="v4 pair T12")
    batch({"MODE": "pair", "T_MAX": 99.0}, label="v4 pair no fallback")
