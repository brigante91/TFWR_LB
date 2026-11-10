"""Offline prototype: how fast is hay if a drone knows the next companion roll?

One drone, a cluster of grass cells surrounded by companion plants laid out with a
periodic colouring. Each harvest consumes the next roll (type, dx, dy); the drone
picks which grass cell takes it. Costs: harvest 200, move 200 per step, plus a
per-harvest compute overhead for the prediction itself.
"""
import random, sys

OFFS = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) if 0 < abs(dx) + abs(dy) <= 3]


def run(cells, ncol, grow, overhead, steps=40000, predict=True, seed=1):
    rnd = random.Random(seed)
    grass = set(cells)
    # colour of a companion cell; type t in 0..2 (bush, carrot, tree). With ncol == 2
    # only bush/tree are planted, so a carrot roll (t == 1) can never be satisfied.
    if ncol == 3:
        col = lambda x, y: (x + 2 * y) % 3
    else:
        col = lambda x, y: 2 * ((x + y) % 2)
    def fits(c, roll):
        t, dx, dy = roll
        tgt = (c[0] + dx, c[1] + dy)
        return tgt not in grass and col(*tgt) == t
    sat = {c: False for c in cells}
    ready = {c: 0 for c in cells}          # tick at which the grass is grown
    pos = cells[0]; t = 0; good = 0
    for _ in range(steps):
        dx, dy = rnd.choice(OFFS); roll = (rnd.randrange(3), dx, dy)
        best = None
        for c in cells:
            d = 200 * (abs(c[0] - pos[0]) + abs(c[1] - pos[1]))
            f = fits(c, roll) if predict else None
            if predict:
                if sat[c] and f:      rank, wait = 0, max(0, ready[c] - (t + d))   # productive and stays good
                elif not sat[c] and f: rank, wait = 1, 0                            # repair a broken cell
                elif not sat[c]:       rank, wait = 2, 0                            # burn the roll on a broken cell
                else:                  rank, wait = 3, max(0, ready[c] - (t + d))  # productive but breaks the cell
            else:
                rank, wait = (0 if sat[c] else 1), (max(0, ready[c] - (t + d)) if sat[c] else 0)
            key = (rank, d + wait)
            if best is None or key < best[0]: best = (key, c, d, wait)
        _, c, d, wait = best
        t += d + wait + overhead
        if sat[c] and t >= ready[c]: good += 1
        sat[c] = fits(c, roll)
        ready[c] = t + grow          # effect happens when the action starts
        t += 200; pos = c
    return t / good


def secs(tpg, drones=32):
    return 2e9 / 81920 * tpg / drones / 6075


layouts = {
    'row2': [(0, 0), (1, 0)],
    'row3': [(0, 0), (1, 0), (2, 0)],
    'row4': [(0, 0), (1, 0), (2, 0), (3, 0)],
    '2x2': [(0, 0), (1, 0), (0, 1), (1, 1)],
    'row6': [(i, 0) for i in range(6)],
    '2x3': [(i, j) for j in range(2) for i in range(3)],
    '3x3': [(i, j) for j in range(3) for i in range(3)],
}
if __name__ == '__main__':
    grow = 759
    print('baseline (no prediction, all bush, row2):  %.0f ticks/good -> %.1f s' % ((lambda v: (v, secs(v)))(run(layouts['row2'], 1, grow, 20, predict=False))) if False else '', end='')
    print('ticks per good harvest (run time in s for 32 drones, without setup)')
    for ncol in (2, 3):
        for oh in (0, 100, 300):
            row = []
            for name, cells in layouts.items():
                v = run(cells, ncol, grow, oh)
                row.append(f'{name}:{v:5.0f}({secs(v):4.0f}s)')
            print(f'types={ncol} overhead={oh:<3}', '  '.join(row))
