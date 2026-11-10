"""Modello tick-per-tick di lb_pumpkins_v2.py sul simulatore pumpsim (per la taratura)."""
import sys
from pumpsim import *


def water_to(d, target):
    # w = get_water(); need = (target-w)*4; n = need//1; if n<need: n+=1; while n>0: if use_item...
    w = d.get_water()
    need = (target - w) * 4
    n = int(need // 1)
    cost = 1 + 2 + 1 + 2
    if n < need:
        n += 1
        cost += 1
    cost += 1
    while n > 0:
        cost += 1
        r = d.water(n)
        cost += r
        if r == ACT:
            return cost
        n -= 1
        cost += 1
    return cost


def replant(d):
    cost = 1 + d.plant() + 1
    tank = d.num_water()
    if tank >= 60:
        cost += 1 + water_to(d, 1.0)
    elif tank >= 2:
        cost += 2 + water_to(d, 0.5)
    else:
        cost += 2
    return cost


def plant_fresh(d):
    cost = 1 + d.plant() + 1
    tank = d.num_water()
    if tank >= 400:
        cost += 1 + water_to(d, 1.0)
    elif tank >= 150:
        cost += 2 + water_to(d, 0.5)
    elif tank >= 30:
        cost += 3 + water_to(d, 0.25)
    else:
        cost += 3
    return cost


def step_cost(d, n):
    # step(n): n = n % S; if n <= S//2: for: move(North) else: for: move(South)
    n = n % S
    cost = 1 + 1 + 2
    if n <= S // 2:
        for _ in range(n):
            cost += 1 + d.move(N)
    else:
        for _ in range(S - n):
            cost += 1 + d.move(So)
    return cost


def fill(d, first):
    pending = []
    yield 1
    for i in range(S):
        c = 1  # for
        if first:
            c += 2
            if not d.cell().soil:
                c += d.till()
        else:
            c += 1
        t = d.get_entity_type()
        c += 1 + 2
        if t == DEAD:
            c += d.harvest()
            t = NONE
        c += 2
        if t == NONE:
            c += plant_fresh(d)
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
            c = 1 + 2 + step_cost(d, i - pos)
            pos = i
            t = d.get_entity_type()
            c += 1 + 2
            if t == DEAD:
                c += d.harvest() + replant(d)
                left.append(i)
                c += 1
                yield c
            elif t == NONE:
                yield c + 2
                return pos
            else:
                c += 2 + 1
                if d.can_harvest():
                    yield c
                    continue
                c += 2
                if len(pending) <= 3:
                    yield c + 1
                    # while True: t = get_entity_type(); if DEAD: ...; elif None: return; elif can_harvest: break
                    while True:
                        t = d.get_entity_type()
                        if t == DEAD:
                            yield 3 + d.harvest() + replant(d)
                        elif t == NONE:
                            yield 5
                            return pos
                        elif t == RIPE:
                            yield 7
                            break
                        else:
                            yield from d.wait_cell(7, GROWING)
                else:
                    left.append(i)
                    yield c + 1
        pending = left
        yield 2
    return pos


def goto_x(d, x):
    cost = 2
    if x <= S // 2:
        for _ in range(x):
            cost += 1 + d.move(E)
    else:
        for _ in range(S - x):
            cost += 1 + d.move(W)
    return cost


def worker(x):
    def prog(d):
        yield goto_x(d, x)
        first = True
        while True:
            yield from fill(d, first)
            first = False
            # while get_entity_type() != None: pass
            while d.get_entity_type() != NONE:
                yield from d.wait_cell(3, d.get_entity_type())
            yield 3
    return prog


def spawn_range(lo, hi):
    def prog(d):
        a, b = lo, hi
        while b - a > 1:
            mid = (a + b) // 2
            yield 4 + d.spawn(spawn_range(mid, b))
            b = mid
        yield from worker(a)(d)
    return prog


def main_prog(d):
    yield ACT  # clear()
    yield 2 + d.spawn(spawn_range(1, S))
    first = True
    c = 0
    while True:
        yield from fill(d, first)
        first = False
        t_fill = d.w.t
        # while measure() != measure(West): pass  (3 tick a iterazione)
        yield from d.wait_complete(3)
        t_ok = d.w.t
        before = d.w.pumpkins
        yield 3 + d.harvest()
        c += 1
        d.w.log.append((c, t_fill / TPS, t_ok / TPS, d.w.pumpkins - before, d.w.tank()))
        yield 6
        if d.w.done:
            return


def run(seed=0, dev=0.2, verbose=False):
    w = World(seed, dev=dev)
    w.run(main_prog)
    if verbose:
        for c, tf, tok, y, tank in w.log:
            if c <= 10 or c % 10 == 0 or c == len(w.log):
                print("ciclo %d colonna finita a %.2f campo completo a %.2f raccolto %d acqua %d" % (c, tf, tok, y, tank))
    return w


if __name__ == "__main__":
    dev = float(sys.argv[1]) if len(sys.argv) > 1 else 0.2
    for seed in range(3):
        w = run(seed, dev, verbose=(seed == 0))
        summarize(w, "v2 seed %d dev %.2f" % (seed, dev))
