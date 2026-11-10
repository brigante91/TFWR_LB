"""Regime di Hay_Single con costi riga per riga, varianti appaiate (stessi companion e stessa acqua).
V1  : come lb_hay_single_v1 (flag fast, acqua ogni 8 cicli sulla prima visita se < T).
V2  : senza flag: la cella successiva e' scritta dentro i due rami (if valido al primo colpo / else).
V2W : V2 + acqua solo nel ramo 'valido al primo colpo': if get_water() < T: use_item(WATER, 4), e
      in quel caso la cella successiva non controlla can_harvest (gap >= 809 tick).
Costi: azione 200, chiamata get_* 1, `in` 3, if 1, while 1 alla prima valutazione."""
import random, math, statistics, sys
GROW = 3037.5; WDT = 6075 * 20 / 512; P = 23 / 72; NEED = 1221


class Cell:
    def __init__(s, rng):
        s.w = 1.0; s.t = 0.0; s.prog = 1.0; s.rng = rng

    def upd(s, now):
        if now <= s.t:
            return
        n = int(now // 607.5) - int(s.t // 607.5)
        k = sum(1 for _ in range(n) if s.rng.random() < 0.1)
        w0 = s.w; w1 = w0 * 0.99 ** k
        s.prog = min(1.0, s.prog + (now - s.t) * (1 + 2 * (w0 + w1)) / GROW)
        s.w = w1; s.t = now

    def wait(s, now):
        s.upd(now)
        if s.prog >= 1:
            return 0
        return (1 - s.prog) * GROW / (1 + 4 * s.w)


def run(seed, mode, T=0.9):
    crng = random.Random(seed)
    cells = [Cell(random.Random(seed * 7 + 1)), Cell(random.Random(seed * 7 + 2))]
    t = 13000.0
    for c in cells:
        c.t = t
    used = 0; valid = 0; i = 0; check = mode != "V3"; waited = 0; nw = 0; cyc = 0; unripe = 0

    def water(c):
        nonlocal t, used, nw
        if int(t / WDT) - used >= 4:
            used += 4; c.upd(t); c.w = min(1.0, c.w + 1.0); t += 200; nw += 1
        else:
            t += 1

    while valid < NEED:
        c = cells[i]
        if mode == "V1":
            t += 1                                   # if fast
        if check:
            t += 2                                   # while not can_harvest (prima valutazione)
            wt = c.wait(t)
            if wt > 0:
                n = math.ceil(wt / 2) * 2; waited += n; t += n
        else:
            c.upd(t)
            if c.prog < 1:
                unripe += 1
        if c.wait(t) <= 0:
            valid += 1
        c.prog = 0.0; c.t = t; t += 200              # harvest
        if mode == "V1" and cyc % 8 == 0 and i == 0 or mode == "V1" and cyc % 8 == 0 and i == 1:
            t += 3
            if c.w < T:
                water(c)
        t += 5                                       # if get_companion() in ok
        first = crng.random() < P
        if first:
            nxt_check = mode != "V3"
            if mode in ("V2W", "V3"):
                t += 3
                if c.w < T:
                    water(c); nxt_check = False
        else:
            nxt_check = False
            t += 200 + 5                             # harvest + while (prima valutazione)
            last = t - 205
            while crng.random() >= P:
                last = t; t += 204
            c.upd(t); c.prog = 0.0; c.t = last
        t += 200                                     # move
        check = nxt_check
        i ^= 1
        if i == 0:
            cyc += 1
    return t / 6075, waited / 6075, nw, unripe


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    base = [run(s, "V1") for s in range(n)]
    for mode, T in [("V2W", 0.85), ("V3", 0.75), ("V3", 0.8), ("V3", 0.85), ("V3", 0.9)]:
        r = [run(s, mode, T) for s in range(n)]
        d = [a[0] - b[0] for a, b in zip(r, base)]
        print("%-4s T=%.2f  tempo %.3f  diff %+.3f +- %.3f  attesa %.3f  acqua %.1f  acerbi %.2f" % (
            mode, T, statistics.mean(x[0] for x in r), statistics.mean(d), statistics.stdev(d) / n ** .5 if any(d) else 0,
            statistics.mean(x[1] for x in r), statistics.mean(x[2] for x in r), statistics.mean(x[3] for x in r)))
