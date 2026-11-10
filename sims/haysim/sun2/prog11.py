"""Schema v11 per la classifica Sunflowers (32 droni), per sim3.simulate.

Differenze dalla v10 (sunprog.run7), ognuna con il suo flag:
  MERGE15 : niente finestra per il 15. Dopo la scadenza della semina (tp) non si fanno piu'
            rilanci (il flag resta pulito) e ogni drone raccoglie i suoi 15 nell'attesa di
            crescita [tp, th]; la prima finestra a tempo e' quella del 14.
  DEFER   : nelle fasi, cella non ancora cresciuta -> rimandata a fine giro e attesa fino a
            poco prima della fine della finestra (invece di raccoglierla da seme).
  PREPOS  : nel tempo morto di una fase il drone va al capo piu' vicino della lista successiva
            (o all'angolo di partenza della semina dopo l'ultima fase).
  CASC    : dopo ogni 15 raccolto ripianta subito (nessun seme puo' superare 15).
  PW_LIST / GW_LIST / PH_LIST : finestre diverse nei primi round.
  JIT     : ritardo massimo delle attese (200 = get_time, ~4 = get_tick_count).
Costi dell'interprete come in sunprog (azione 200, operatore/confronto/indice 1, chiamata 1).
"""
import os
import random as _r
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim3
from sim3 import simulate

GOAL0 = sim3.GOAL
S = 32
BW, BH = 4, 8
ORDER0 = [0, 1, 2, 3, 7, 6, 5, 4, 8, 9, 10, 11, 15, 14, 13, 12, 16, 17, 18, 19, 23, 22, 21, 20, 24, 25, 26, 27, 31, 30, 29, 28]
ORDER31 = ORDER0[::-1]

DEF = dict(MINV=9, CAP=6, P_W=3.8, P_W0=10.5, G_W=1.0, G_W0=4.5, PH_W=0.85, PH_W0=1.5,
           PW_LIST=None, GW_LIST=None, PH_LIST=None, NO15=1.5, D15=0.3, MG=0.05, MD=0.06, STEP=0.12,
           WF=7.0, WL=7.0, STOP_AT=GOAL0 + 10, MERGE15=True, DEFER=True, PREPOS=True,
           CASC=False, CASC_MAXU=13, JIT=200.0, SKIP=None, LATE14=False, WMAX=4, RANDGOAL=True,
           CAP15=None, WF15=None, BOOT=None, LMIN=1.5, LMIN_LIST=None, WB=None, PACE=False, TAU=0.075, WFL_LIST=None)

ST = {}


def stat(k, v=1):
    ST[k] = ST.get(k, 0) + v


class C:
    __slots__ = ("o", "a", "ox", "oy", "x", "y")

    def __init__(s):
        s.o = 0
        s.a = 0
        s.x = 0
        s.y = 0

    def r(s, *a):
        t = (s.a + s.o,) + a
        stat('code', s.o)
        stat('moves', s.a)
        s.o = 0
        s.a = 0
        return t


def dist(a, b):
    return abs(a % BW - b % BW) + abs(a // BW - b // BW)


def go(c, k, cur):
    m = dist(k, cur)
    c.o += 13 + 2 * m
    c.a += 200 * m
    return k


def goto(c, tx, ty):
    dx = (tx - c.x) % S
    n = dx if dx <= S // 2 else S - dx
    dy = (ty - c.y) % S
    n2 = dy if dy <= S // 2 else S - dy
    c.o += 16 + n + n2
    c.a += 200 * (n + n2)
    c.x, c.y = tx, ty


def cell(c, k):
    return (c.oy + k // BW) * S + c.ox + k % BW


def wait(c, tgt, cat):
    c.o += 3
    t = yield c.r('time')
    if t < tgt:
        stat('idle_' + cat, tgt - t)
        yield c.r('wait', tgt)


def due(P, v, tp, th, phl):
    # istante entro cui una cella di valore v deve essere cresciuta
    if P['MERGE15']:
        if v == 15:
            return th - P['D15']
        return th + sum(phl[:14 - v])
    return th + sum(phl[:15 - v])


def plant_cell(c, P, k, tp, th, phl, lst, lmin, rem, wk, last, wfl=None):
    MINV, CAP = P['MINV'], P['CAP']
    merge = P['MERGE15']
    wb = P['WB']
    tlim = tp - rem * P['TAU'] if P['PACE'] else tp
    tflag = tp if merge else th - 0.3
    v = yield c.r('plant', cell(c, k))
    stat('plant')
    c.o += 1 + 4
    while True:
        t = yield c.r('time')
        c.o += 2
        if v < MINV:
            kind = 1
        else:
            i = v - MINV
            c.o += 7
            if due(P, v, tp, th, phl) - t < lmin:
                kind = 2
            else:
                c.o += 4
                if len(lst[i]) >= CAP:
                    kind = 3
                elif wb is not None and len(lst[i]) > 0:
                    c.o += 12
                    kind = 3 if wk[i] + dist(last[i], k) * 200 + 215 > wb else 0
                else:
                    kind = 0
        c.o += 1
        if kind == 0:
            break
        c.o += 1
        if t < tlim:
            yield c.r('harv', cell(c, k))
            stat('reroll')
            v = yield c.r('plant', cell(c, k))
            stat('plant')
            c.o += 1
            continue
        c.o += 2
        if kind == 1:
            stat('junk_left')
            break
        if t < tflag:
            yield c.r('harv', cell(c, k))
            stat('removed')
            return 0
        stat('kept_bad')
        break
    c.o += 2
    if v >= MINV:
        t = yield c.r('time')
        left = due(P, v, tp, th, phl) - t
        c.o += 8
        if left < (wfl[1] if wfl else P['WL']):
            w = yield c.r('getw', cell(c, k))
            wf = wfl[0] if wfl else P['WF']
            if left <= 0.05:
                x = 9.0
            else:
                x = wf / left - 1 - 4 * w
            c.o += 7
            add = x // 1
            if add < x:
                add += 1
                c.o += 1
            c.o += 2
            if add > P['WMAX']:
                add = P['WMAX']
            if add > (1 - w) * 4 + 0.999:
                add = int((1 - w) * 4 + 0.999)
            c.o += 2
            if add > 0:
                ok = yield c.r('water', cell(c, k), int(add))
                stat('water' if ok else 'waterfail')
                c.o += 1
                if not ok:
                    c.o += 2
                    if add > 1:
                        ok = yield c.r('water', cell(c, k), 1)
                        stat('water' if ok else 'waterfail')
    return v


def sweep(c, P, lst, cur, first, tp, th, phl, has, lmin, wfl=None):
    MINV = P['MINV']
    c.o += 4
    order = ORDER0 if cur == 0 else ORDER31
    skip = P['SKIP']
    rem = 32
    wk = [0] * (16 - MINV)
    last = [0] * (16 - MINV)
    c.o += 4
    for k in order:
        c.o += 1
        if skip is not None and not first:
            tn = yield c.r('time')
            c.o += 3
            if tn >= th - skip:
                stat('skipped')
                continue
        c.o += 2
        if k != order[0]:
            c.o += 2
            c.a += 200
        cur = k
        if first:
            c.o += 4
            c.a += 200
            has[k] = False
        c.o += 3
        if has[k]:
            yield c.r('harv', cell(c, k))
            stat('junkharv')
        c.o += 1
        rem -= 1
        v = yield from plant_cell(c, P, k, tp, th, phl, lst, lmin, rem, wk, last, wfl)
        c.o += 3
        if v >= MINV:
            i = v - MINV
            if P['WB'] is not None:
                c.o += 10
                if len(lst[i]) > 0:
                    wk[i] += dist(last[i], k) * 200 + 215
                else:
                    wk[i] = 215
                last[i] = k
            lst[i].append(k)
            c.o += 3
            has[k] = False
        else:
            has[k] = v != 0
    return cur


def stopchk(c, P):
    c.o += 2
    p = yield c.r('num')
    return p >= P['STOP_AT']


def phase15(c, P, lst, cur, tp, th, phl, has):
    # raccolta dei 15 nell'attesa di crescita: in ordine di semina, aspettando la crescita
    MINV = P['MINV']
    L = lst[15 - MINV]
    c.o += 5
    if len(L) == 0:
        return cur
    cur = go(c, L[0], cur)
    yield from wait(c, tp, 'P')
    dl = th - P['MG']
    j = len(L)
    for k in L:
        c.o += 1
        cur = go(c, k, cur)
        c.o += 5
        j -= 1
        t0 = yield c.r('time')
        ok = yield c.r('gwait', cell(c, k), dl - j * P['STEP'])
        t1 = yield c.r('time')
        stat('idle_15', t1 - t0)
        yield c.r('harv', cell(c, k))
        stat('h15' if ok else 'h15_seed')
        if (yield from stopchk(c, P)):
            return -1
        if P['CASC']:
            tn = yield c.r('time')
            c.o += 3
            if tn < dl - 0.1:
                u = yield c.r('plant', cell(c, k))
                stat('cplant')
                c.o += 1 + 4
                if u == 15:
                    # e' il massimo: toglierlo non sporca il flag
                    yield c.r('harv', cell(c, k))
                    stat('creroll')
                elif u >= MINV:
                    lu = lst[u - MINV]
                    # inserimento in ordine di serpentina (posizione di k nell'ordine corrente)
                    c.o += 4 + 3 * len(lu)
                    lu.append(k)
                    stat('ckeep')
                    if u <= P['CASC_MAXU']:
                        left = due(P, u, tp, th, phl) - tn
                        w = yield c.r('getw', cell(c, k))
                        x = P['WF'] / max(left, 0.05) - 1 - 4 * w
                        add = min(P['WMAX'], int(x) + (1 if x > int(x) else 0))
                        c.o += 12
                        if add > 0:
                            ok = yield c.r('water', cell(c, k), int(add))
                            stat('water' if ok else 'waterfail')
                else:
                    has[k] = True
                    c.o += 2
    del L[:]
    c.o += 1
    return cur


def prepos(c, P, L, cur, tend):
    # nel tempo morto: vai al capo piu' vicino della prossima lista; ritorna (cur, verso)
    c.o += 4
    n = len(L)
    if n == 0:
        return cur, 1
    a, b = L[0], L[-1]
    da, db = dist(a, cur), dist(b, cur)
    c.o += 20
    if da <= db:
        tg, d, m = a, 1, da
    else:
        tg, d, m = b, -1, db
    if P['PREPOS'] and m > 0:
        tn = yield c.r('time')
        c.o += 4
        if tn + m * 0.036 < tend:
            cur = go(c, tg, cur)
            stat('premoves', m)
    return cur, d


def phase(c, P, L, cur, d, tend):
    c.o += 4
    j = len(L)
    if j == 0:
        return cur
    seq = L if d > 0 else L[::-1]
    c.o += 2
    for k in seq:
        c.o += 1 if d > 0 else 3
        cur = go(c, k, cur)
        j -= 1
        if P['DEFER']:
            c.o += 3
            ok = yield c.r('canh', cell(c, k))
            if not ok:
                # non cresciuta: aspetta qui finche' il resto della lista ci sta ancora
                c.o += 4
                t0 = yield c.r('time')
                ok = yield c.r('gwait', cell(c, k), tend - P['MD'] - j * P['STEP'])
                t1 = yield c.r('time')
                stat('idle_defer', t1 - t0)
                stat('hdefer' if ok else 'hdefer_seed')
        yield c.r('harv', cell(c, k))
        stat('hph')
        if (yield from stopchk(c, P)):
            return -1
    del L[:]
    c.o += 1
    return cur


def lget(lst, i, dflt):
    if lst is not None and i < len(lst) and lst[i] is not None:
        return lst[i]
    return dflt


def run11(c, P, b, t0, main):
    MINV = P['MINV']
    NL = 16 - MINV
    c.ox, c.oy = BW * (b % 8), BH * (b // 8)
    goto(c, c.ox, c.oy)
    lst = [[] for _ in range(NL)]
    has = [True] * 32
    c.o += 12
    cur, t, r = 0, t0, 0
    merge = P['MERGE15']
    while True:
        c.o += 8
        if r == 0:
            pw, gw = P['P_W0'], P['G_W0']
        else:
            pw, gw = lget(P['PW_LIST'], r - 1, P['P_W']), lget(P['GW_LIST'], r - 1, P['G_W'])
        nph = NL - 1 if merge else NL
        phl = [P['PH_W']] * nph
        pl = lget(P['PH_LIST'], r - 1, None) if r > 0 else None
        if pl is not None:
            phl = [pl] * nph if not isinstance(pl, list) else pl
        if r == 0:
            phl[0] = P['PH_W0']
        tp = t + pw
        th = tp + gw
        c.o += 3
        cur = go(c, 0 if cur // BW < BH // 2 else 31, cur)
        cur = yield from sweep(c, P, lst, cur, r == 0, tp, th, phl, has, lget(P['LMIN_LIST'], r, P['LMIN']), lget(P['WFL_LIST'], r, None))
        if main:
            tn = yield c.r('time')
            stat('sweep_end_main', tn - tp)
        tn = yield c.r('time')
        stat('late_sweep', 1 if tn > tp else 0)
        vtop = 15
        if merge:
            cur = yield from phase15(c, P, lst, cur, tp, th, phl, has)
            if cur < 0:
                yield c.r('clear')
                return
            vtop = 14
        # pre-posizionamento sulla prima lista
        cur, d = yield from prepos(c, P, lst[vtop - MINV], cur, th)
        yield from wait(c, th, 'G')
        v = vtop
        i = 0
        c.o += 2
        while v >= MINV:
            c.o += 4
            tend = th + phl[i]
            cur = yield from phase(c, P, lst[v - MINV], cur, d, tend)
            if cur < 0:
                yield c.r('clear')
                return
            c.o += 3
            if v > MINV:
                cur, d = yield from prepos(c, P, lst[v - 1 - MINV], cur, tend)
            elif P['PREPOS']:
                tg = 0 if cur // BW < BH // 2 else 31
                m = dist(tg, cur)
                tn = yield c.r('time')
                c.o += 8
                if m > 0 and tn + m * 0.036 < tend:
                    cur = go(c, tg, cur)
                    stat('premoves', m)
            th = tend
            yield from wait(c, th, 'H')
            v -= 1
            i += 1
        t = th
        r += 1
        if main:
            stat('rounds')


def spawn_range(c, P, lo, hi, t0):
    c.o += 2
    while True:
        c.o += 2
        if not hi - lo > 1:
            break
        mid = (lo + hi) // 2
        c.o += 4
        yield c.r('spawn', task(P, mid, hi, t0))
        hi = mid
    yield from run11(c, P, lo, t0, False)


def task(P, lo, hi, t0):
    def mk(d):
        return spawn_range(C(), P, lo, hi, t0)
    return mk


def main_prog(d, P, main):
    c = C()
    t0 = yield c.r('time')
    c.o += 2
    yield c.r('spawn', task(P, 1, 32, t0))
    yield from run11(c, P, 0, t0, True)


def sim11(P, seed, stats=False):
    Q = dict(DEF)
    Q.update(P)
    g = GOAL0
    if Q['RANDGOAL']:
        g = int(GOAL0 * (0.9 + 0.2 * _r.Random(seed * 7 + 3).random()))
    Q['STOP_AT'] = g + 10
    ST.clear()
    r = simulate(main_prog, Q, seed, goal=g, jit=Q['JIT'])
    r['t_raw'] = r['t']
    r['t'] = r['t'] * GOAL0 / g
    if stats:
        r['st'] = dict(ST)
    return r


def ev(P, n=16, seeds=None):
    import statistics as SS
    ts = []
    for s in (seeds or range(n)):
        r = sim11(P, s)
        ts.append(r['t'] if r['ok'] else 999.0)
    return SS.mean(ts), SS.stdev(ts) / len(ts) ** .5


if __name__ == '__main__':
    import time
    t0 = time.time()
    r = sim11({}, 0, stats=True)
    print(r['t'], r['t_raw'], r['ok'], 'boost', r['boost'], 'plain', r['plain'], 'zero', r['zero'],
          'lost', r['lost'], 'zmax', r['zmax'], 'notmax', r['notmax'], 'tank', r['tank'])
    print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in sorted(r['st'].items())})
    print(time.time() - t0)
