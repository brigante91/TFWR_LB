# trascrizione di lb_rice.py v1
from world import *
def make_path(S, D, d):
    x0 = d*S//D; x1 = (d+1)*S//D; cells = []
    for c in range(x0, x1):
        ys = range(S) if (c-x0) % 2 == 0 else range(S-1, -1, -1)
        cells += [(c, y) for y in ys]
    return cells
def prog(w, d, D, r):
    S = w.S; cells = make_path(S, D, d); OV = 5*OP
    water_plant = len(cells) < 40
    yield ACT * (d % 6)
    def dig_to_clay(x, y):
        n = 0
        while w.top(x, y) != "clay" and n < 40:
            yield w.dig(x, y) + OV; n += 1
        w.plant(x, y, r); yield ACT
    first = True
    while True:
        for (x, y) in cells:
            if first or w.ent[x][y] is None:
                yield from dig_to_clay(x, y)
            else:
                while not w.grown(x, y):
                    yield 0.01
                w.rice += 128; w.ent[x][y] = None; yield ACT + OV
                if w.rice >= w.goal: return
                yield w.dig(x, y)
                if not w.plant(x, y, r): yield from dig_to_clay(x, y)
                else: yield ACT
            if water_plant and w.water[x][y] < 0.07 and w.tank_get():
                w.add_water(x, y); yield ACT
            yield ACT + OV
        first = False
if __name__ == "__main__":
    import sys
    for mode, S, D in (("multi", 32, 32), ("single", 8, 1)):
        ts = []
        for s in range(3):
            World.goal = GOALS[mode]
            t, w = run(S, D, prog, s, GOALS[mode]); ts.append(t)
            print(mode, s, round(t, 1), "persi", w.lost, flush=True)
