"""Strategia v3 (campo 32x32, un drone per colonna, barriera del main) parametrizzata.

Parametri (dict P):
  WLOW/WTGT   : nella passata di riempimento, se acqua cella < WLOW e serbatoio >= RES, porta a WTGT
  RES         : riserva minima del serbatoio per annaffiare le fresche
  WREP        : acqua obiettivo per le ripiantate (0 = nessuna), solo se serbatoio >= RESREP
  WREP_K      : ripiantate annaffiate solo se le celle pendenti sono <= WREP_K (0 = sempre)
  WAIT_K      : con <= WAIT_K celle pendenti il drone aspetta sul posto invece di fare la spola
  FERT_T      : se il ciclo dura da piu' di FERT_T secondi (dall'inizio del riempimento) usa il
                fertilizzante sulle celle pendenti (morte appena ripiantate o in crescita)
  FERT_K      : fertilizzante solo se celle pendenti <= FERT_K
  FERT_GEN    : fertilizzante solo su celle con almeno FERT_GEN morti nel ciclo
  RING        : True = la passata sulle pendenti procede sempre verso Nord (anello), False = step corto
"""
import sys
from pumpsim import *

DEFAULT = dict(WLOW=0.5, WTGT=1.0, RES=0, WREP=1.0, WREP_K=0, RESREP=0, WAIT_K=2,
               FERT_T=99.0, FERT_K=2, FERT_GEN=1, RING=False, WPASS=0.0)


def water_up(d, target):
    """get_water(); n = unita' per arrivare a target; use_item(Water, n) se il serbatoio basta,
    altrimenti prova con quello che c'e'. Ritorna i tick."""
    w = d.get_water()
    need = (target - w) * 4
    n = int(need // 1)
    cost = 7
    if n < need:
        n += 1
    if n <= 0:
        return cost
    tank = d.num_water()
    cost += 2
    if tank < n:
        n = tank
        if n <= 0:
            return cost
    return cost + d.water(n)


def step(d, n, ring):
    n = n % S
    cost = 5
    if ring or n <= S // 2:
        for _ in range(n):
            cost += 1 + d.move(N)
    else:
        for _ in range(S - n):
            cost += 1 + d.move(So)
    return cost


def worker_cycle(d, P, first, gens):
    """Un ciclo del worker: riempimento della colonna (dalla cella corrente verso Nord) e
    passate sulle celle pendenti finche' tutte sono mature o il main ha raccolto (cella None)."""
    t0 = d.w.t
    pending = []
    yield 2
    for i in range(S):
        c = 1
        if first:
            c += 2
            if not d.cell().soil:
                c += d.till()
        else:
            c += 1
        t = d.get_entity_type()
        c += 3
        if t == DEAD:
            c += d.harvest()
            t = NONE
        c += 2
        if t == NONE:
            gens[i] = 0
            c += d.plant() + 2
            if d.get_water() < P["WLOW"] and d.num_water() >= P["RES"]:
                c += water_up(d, P["WTGT"])
            pending.append(i)
            c += 1
        else:
            c += 2
            if not d.can_harvest():
                pending.append(i)
                c += 1
        c += d.move(N)
        yield c
    pos = 0
    yield 2
    while len(pending) > 0:
        left = []
        yield 2
        for i in pending:
            c = 3 + step(d, i - pos, P["RING"])
            pos = i
            c += 3
            while True:
                t = d.get_entity_type()
                c += 3
                if t == RIPE:
                    yield c
                    break
                if t == NONE:
                    yield c
                    return
                late = (d.w.t - t0) / TPS > P["FERT_T"] and len(pending) <= P["FERT_K"]
                if t == DEAD:
                    gens[i] += 1
                    c += d.harvest() + d.plant() + 3
                    if late and gens[i] >= P["FERT_GEN"] and d.num_fert() >= 1:
                        c += 2 + d.fertilize(1)
                        yield c
                        c = 0
                        continue
                    if P["WREP"] > 0 and (P["WREP_K"] == 0 or len(pending) <= P["WREP_K"]) and d.num_water() >= P["RESREP"]:
                        c += 3 + water_up(d, P["WREP"])
                    if len(pending) > P["WAIT_K"]:
                        left.append(i)
                        yield c + 1
                        break
                    yield c
                    c = 0
                    continue
                # in crescita
                if late and gens[i] >= P["FERT_GEN"] and d.num_fert() >= 1:
                    c += 2 + d.fertilize(1)
                    yield c
                    c = 0
                    continue
                if len(pending) > P["WAIT_K"]:
                    left.append(i)
                    yield c + 1
                    break
                if P["WPASS"] > 0 and d.get_water() < P["WPASS"]:
                    c += 2 + water_up(d, 1.0)
                yield c
                c = 0
                yield from d.wait_cell(7, GROWING)
        pending = left
        yield 2


def worker(x, P):
    def prog(d):
        cost = 2
        if x <= S // 2:
            for _ in range(x):
                cost += 1 + d.move(E)
        else:
            for _ in range(S - x):
                cost += 1 + d.move(W)
        yield cost
        first = True
        gens = [0] * S
        while True:
            yield from worker_cycle(d, P, first, gens)
            first = False
            while d.get_entity_type() != NONE:
                yield from d.wait_cell(3, d.get_entity_type())
            yield 3
    return prog


def spawn_range(lo, hi, P):
    def prog(d):
        a, b = lo, hi
        while b - a > 1:
            mid = (a + b) // 2
            yield 4 + d.spawn(spawn_range(mid, b, P))
            b = mid
        yield from worker(a, P)(d)
    return prog


def make_main(P):
    def main_prog(d):
        yield ACT  # clear()
        yield 2 + d.spawn(spawn_range(1, S, P))
        first = True
        gens = [0] * S
        c = 0
        while True:
            yield from worker_cycle(d, P, first, gens)
            first = False
            t_fill = d.w.t
            yield from d.wait_complete(3)
            t_ok = d.w.t
            before = d.w.pumpkins
            yield 3 + d.harvest()
            c += 1
            d.w.log.append((c, t_fill / TPS, t_ok / TPS, d.w.pumpkins - before, d.w.tank()))
            yield 6
            if d.w.done:
                return
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
        tots.append(w.harvests[-1][0] / TPS)
    m = sum(tots) / len(tots)
    print("%-44s media %6.1f s (%d:%04.1f)  [%s]" % (label or str(P), m, m // 60, m % 60,
                                                   " ".join("%.1f" % t for t in tots)))
    return m


if __name__ == "__main__":
    batch({}, label="default")
