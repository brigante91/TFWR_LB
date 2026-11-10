"""Simulatore del regime di Hay_Single (1 drone, 2 erbe A e C adiacenti, cespugli su tutto il resto
dei due rombi). Costi come in dsim (FINDINGS_cactus_dino_maze.md): azione 200, get_*/can_harvest 1,
`x in dict` 3, if 1, while 1 alla prima valutazione.
Erba: crescita 3037.5/(1+4w) tick; acqua: decadimento 0.99 con prob. 0.1 ogni 607.5 tick (stocastico);
serbatoio: +1 ogni 237.3 tick, tutto per un drone.
Codice simulato per ogni visita della cella X (prima: k = raccolti fatti sull'altra cella):
    if fast: while not can_harvest(): pass        (fast = l'altra cella ha trovato al primo colpo)
    harvest()
    [ogni K cicli, su A e C: if get_water() < T: use_item(WATER, 4)]
    if get_companion() in okX: fast = True
    else: fast = False; harvest(); while get_companion() not in okX: harvest()
    move()
Variante SAFE: controllo can_harvest a ogni visita (non solo dopo k = 1).
"""
import random, math, statistics, sys

TPS = 6075.0
GROW = 3037.5
WDT = 6075 * 20 / 512
P = 1 / 3 * 23 / 24
NEED = 1221


class Cell:
    def __init__(s, rng):
        s.w = 0.0; s.t = 0.0; s.prog = 1.0; s.rng = rng

    def upd(s, now):
        if now <= s.t:
            return
        n = int(now // 607.5) - int(s.t // 607.5)
        w0 = s.w
        k = sum(1 for _ in range(n) if s.rng.random() < 0.1)
        w1 = w0 * 0.99 ** k
        s.prog = min(1.0, s.prog + (now - s.t) * (1 + 2 * (w0 + w1)) / GROW)
        s.w = w1; s.t = now

    def ready(s, now):
        s.upd(now)
        if s.prog >= 1:
            return now
        return now + (1 - s.prog) * GROW / (1 + 4 * s.w)


def run(seed, T=0.9, K=4, SAFE=False, setup=12600, W4=4):
    rng = random.Random(seed)
    cells = [Cell(random.Random(seed * 7 + 1)), Cell(random.Random(seed * 7 + 2))]
    t = float(setup)
    used = 0
    for c in cells:
        c.t = t
    valid = 0; fast = False; cyc = 0; wait = 0; unripe = 0; nw = 0
    i = 0
    while valid < NEED:
        c = cells[i]
        if fast or SAFE:
            t += 2
            r = c.ready(t)
            if r > t:
                n = math.ceil((r - t) / 2) * 2
                wait += n; t += n
        else:
            c.upd(t)
            if c.prog < 1:
                unripe += 1
        if c.prog >= 1 or c.ready(t) <= t:
            valid += 1
        c.prog = 0.0; c.t = t
        t += 200
        if cyc % K == 0:
            t += 3
            if c.w < T or cyc == 0:
                if int(t / WDT) - used >= W4:
                    used += W4; c.upd(t); c.w = min(1.0, c.w + 0.25 * W4); t += 200; nw += 1
        t += 5
        if rng.random() < P:
            fast = True
        else:
            fast = False
            t += 200 + 5
            while rng.random() >= P:
                t += 204
            c.upd(t); c.prog = 0.0; c.t = t - 4
        t += 200
        i ^= 1
        if i == 0:
            cyc += 1
            t += 0
    return t / TPS, wait / TPS, unripe, nw


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    for kw in [dict(T=0.95), dict(T=0.9), dict(T=0.85), dict(T=0.8), dict(T=0.7), dict(T=0.9, K=2), dict(T=0.9, K=8), dict(T=0.9, SAFE=True)]:
        r = [run(s, **kw) for s in range(n)]
        print("%-28s tempo %.3f s  attesa %.3f s  acerbi %.2f  azioni acqua %.1f" % (kw, statistics.mean(x[0] for x in r), statistics.mean(x[1] for x in r), statistics.mean(x[2] for x in r), statistics.mean(x[3] for x in r)))
