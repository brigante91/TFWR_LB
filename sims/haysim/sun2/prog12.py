"""Schema 'discesa con ripianto' (v12) per sim3: un round = semina di tutte le celle, poi fasi
15..7; in ogni fase, dopo ogni raccolto si ripianta subito. Il seme nuovo u:
  u < L  -> resta e verra' raccolto nella fase u di QUESTO round (se cresce in tempo)
  u >= L -> tolto subito. Per non rovinare i raccolti degli altri droni tutte le azioni sul
            campo sono allineate a un battito comune di F tick (get_tick_count): rimozioni
            all'istante 0, raccolti a +8, semine a +16: un seme 'velenoso' (u > L) esiste solo
            fra una semina e la rimozione del battito dopo, intervallo senza raccolti.
"""
import os, sys
import random as _r
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim3
from sim3 import simulate
from prog11 import C, stat, ST, dist, go, goto, cell, wait, lget, ORDER0, ORDER31, BW, BH, GOAL0

DEF = dict(P_W=3.4, P_W0=10.0, G_W=1.0, G_W0=4.5, PH=[0.8, 0.8, 0.8, 0.85, 0.9, 0.95, 1.0, 1.0, 1.0],
           PH0X=0.7, GW_LIST=None, PW_LIST=None, LMIN=1.5, LMIN_LIST=None, WF=7.0, WL=7.0, WMAX=4,
           CASC=True, LC=10, LC_LIST=None, F=240, OFF_R=0, OFF_H=8, OFF_P=16, BEAT=True, STEP=0.14, MD=0.06,
           RETRY=0, KEEPGAP=1, CWF=None, STOP_AT=GOAL0 + 10, JIT=200.0, RANDGOAL=True, CASC_FROM=1,
           CMAX=99, MINV=7, CAP=99)


def due(P, v, th, phl):
    # inizio della fase del valore v (phl[0] = fase del 15)
    return th + sum(phl[:15 - v])


def water(c, P, k, left, wf):
    if left < P['WL']:
        w = yield c.r('getw', cell(c, k))
        x = 9.0 if left <= 0.05 else wf / left - 1 - 4 * w
        c.o += 9
        add = int(x) + (1 if x > int(x) else 0)
        add = min(add, P['WMAX'], int((1 - w) * 4 + 0.999))
        c.o += 4
        if add > 0:
            ok = yield c.r('water', cell(c, k), int(add))
            stat('water' if ok else 'waterfail')
            c.o += 1
            if not ok and add > 1:
                c.o += 2
                ok = yield c.r('water', cell(c, k), 1)
                stat('water' if ok else 'waterfail')


def act(c, P, kind, off):
    if P['BEAT']:
        c.o += 8
        yield c.r('align', P['F'], off)


def sweep(c, P, lst, cur, first, tp, th, phl, lmin, has):
    MINV = P['MINV']
    c.o += 6
    order = ORDER0 if cur == 0 else ORDER31
    rem = 32
    for k in order:
        c.o += 3
        if k != order[0]:
            c.o += 2
            c.a += 200
        cur = k
        rem -= 1
        if first:
            c.o += 4
            c.a += 200
            has[k] = False
        c.o += 2
        if has[k]:
            yield c.r('harv', cell(c, k))
            stat('junkharv')
            has[k] = False
        v = yield c.r('plant', cell(c, k))
        stat('plant')
        c.o += 3
        tlim = tp - rem * 0.075
        while True:
            t = yield c.r('time')
            c.o += 8
            bad = v < MINV or due(P, v, th, phl) - t < lmin or len(lst[v - MINV]) >= P['CAP']
            if not (bad and t < tlim):
                break
            yield c.r('harv', cell(c, k))
            stat('reroll')
            v = yield c.r('plant', cell(c, k))
            stat('plant')
            c.o += 1
        if v < MINV:
            has[k] = True
            continue
        t = yield c.r('time')
        c.o += 6
        yield from water(c, P, k, due(P, v, th, phl) - t, P['WF'])
        lst[v - MINV].append(k)
        c.o += 3
    return cur


def phase(c, P, lst, L, cur, tend, th, phl, lc, r):
    MINV = P['MINV']
    todo = lst[L - MINV]
    c.o += 5
    casc = P['CASC'] and L >= lc and r >= P['CASC_FROM']
    nc = 0
    while len(todo) > 0:
        # cella piu' vicina
        c.o += 3 + 9 * len(todo)
        bi = min(range(len(todo)), key=lambda i: dist(todo[i], cur))
        k = todo.pop(bi)
        cur = go(c, k, cur)
        rem = len(todo)
        c.o += 4
        ok = yield c.r('canh', cell(c, k))
        if not ok:
            c.o += 4
            t0 = yield c.r('time')
            ok = yield c.r('gwait', cell(c, k), tend - P['MD'] - rem * P['STEP'])
            t1 = yield c.r('time')
            stat('idle_grow', t1 - t0)
            stat('late_grown' if ok else 'seed_harv')
        yield from act(c, P, 'H', P['OFF_H'])
        yield c.r('harv', cell(c, k))
        stat('harv')
        c.o += 2
        p = yield c.r('num')
        if p >= P['STOP_AT']:
            return -1
        if casc and nc < P['CMAX']:
            tries = 0
            while True:
                tn = yield c.r('time')
                c.o += 5
                if not tn < tend - (rem + 1) * P['STEP'] - 0.09:
                    break
                yield from act(c, P, 'P', P['OFF_P'])
                u = yield c.r('plant', cell(c, k))
                stat('cplant')
                nc += 1
                c.o += 3
                if u <= L - P['KEEPGAP'] and u >= MINV:
                    tn = yield c.r('time')
                    c.o += 6
                    yield from water(c, P, k, due(P, u, th, phl) - tn, P['CWF'] or P['WF'])
                    lst[u - MINV].append(k)
                    c.o += 3
                    stat('ckeep')
                    break
                if u < L:
                    # troppo vicino o sotto MINV: non si puo' togliere senza sporcare il flag
                    if u >= MINV:
                        lst[u - MINV].append(k)
                        c.o += 3
                    stat('ckeep_near')
                    break
                yield from act(c, P, 'R', P['OFF_R'])
                yield c.r('harv', cell(c, k))
                stat('crem_poison' if u > L else 'crem_equal')
                tries += 1
                c.o += 2
                if tries > P['RETRY']:
                    break
    c.o += 1
    return cur


def run12(c, P, b, t0, main):
    MINV = P['MINV']
    NL = 16 - MINV
    c.ox, c.oy = BW * (b % 8), BH * (b // 8)
    goto(c, c.ox, c.oy)
    lst = [[] for _ in range(NL)]
    has = [True] * 32
    c.o += 12
    cur, t, r = 0, t0, 0
    while True:
        c.o += 8
        if r == 0:
            pw, gw = P['P_W0'], P['G_W0']
        else:
            pw, gw = lget(P['PW_LIST'], r - 1, P['P_W']), lget(P['GW_LIST'], r - 1, P['G_W'])
        phl = list(P['PH'])[:NL]
        if r == 0:
            phl[0] += P['PH0X']
        tp = t + pw
        th = tp + gw
        cur = go(c, 0 if cur // BW < BH // 2 else 31, cur)
        cur = yield from sweep(c, P, lst, cur, r == 0, tp, th, phl, lget(P['LMIN_LIST'], r, P['LMIN']), has)
        tn = yield c.r('time')
        stat('late_sweep', 1 if tn > tp else 0)
        yield from wait(c, th, 'G')
        lc = lget(P['LC_LIST'], r, P['LC'])
        for i in range(NL):
            L = 15 - i
            tend = th + phl[i]
            c.o += 5
            cur = yield from phase(c, P, lst, L, cur, tend, th - sum(phl[:i]), phl, lc, r)
            if cur < 0:
                yield c.r('clear')
                return
            tn = yield c.r('time')
            if tn > tend:
                stat('late_phase')
            th = tend
            yield from wait(c, th, 'H')
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
    yield from run12(c, P, lo, t0, False)


def task(P, lo, hi, t0):
    def mk(d):
        return spawn_range(C(), P, lo, hi, t0)
    return mk


def main_prog(d, P, main):
    c = C()
    t0 = yield c.r('time')
    c.o += 2
    yield c.r('spawn', task(P, 1, 32, t0))
    yield from run12(c, P, 0, t0, True)


def sim12(P, seed, stats=False):
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


def ev(P, n=10, seeds=None):
    import statistics as SS
    ts = []
    for s in (seeds or range(n)):
        r = sim12(P, s)
        ts.append(r['t'] if r['ok'] else 999.0)
    return SS.mean(ts), SS.stdev(ts) / len(ts) ** .5


def show(P, seed=0):
    r = sim12(dict(P, RANDGOAL=False), seed, stats=True)
    st = r['st']
    print(P)
    print('  t %.1f ok %s boost %d plain %d zero %d lost %d zmax %d notmax %d tank %d' % (
        r['t'], r['ok'], r['boost'], r['plain'], r['zero'], r['lost'], r['zmax'], r['notmax'], r['tank']))
    print('  ', {k: (round(v, 1) if isinstance(v, float) else v) for k, v in sorted(st.items())})


if __name__ == '__main__':
    show(dict(CASC=False))
    show(dict())
    show(dict(LC=12))
    show(dict(LC=13, KEEPGAP=2))
