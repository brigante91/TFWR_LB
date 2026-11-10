"""Trascrizione di lb_sunflowers_v5.py (e varianti) per sunsim2.simulate, con i costi
dell'interprete riga per riga.  I commenti '# n' danno i tick di codice contati.

Parametri (dict P): P_W, P_W0, G_W, G_W0, PH_W, PH_W0, CAP, MINV, GOAL e i flag delle
varianti:
  ANY_STOP   : ogni drone controlla num_items dopo ogni raccolto e chiama clear() (v7)
  STOP_AT    : soglia di stop (GOAL + margine contro il UsePower fra controllo e fine)
  WFACT      : 6.25 = costante dell'acqua (1+4w >= WFACT/left)
  WLEFT      : soglia 'left < WLEFT' oltre la quale non si annaffia (6.0)
  PHW_LIST   : durata di ogni fase (15..MINV), altrimenti PH_W costante
  NO15_LATE  : 2.0 (rifiuta 15 se mancano meno di x s a th)
  LATE14     : True = dopo la deadline rifiuta v>=14 (come v5)
"""
from sunsim2 import simulate, GOAL as GOAL0

S = 32
BW, BH = 4, 8
ORDER0 = [0, 1, 2, 3, 7, 6, 5, 4, 8, 9, 10, 11, 15, 14, 13, 12, 16, 17, 18, 19, 23, 22, 21, 20, 24, 25, 26, 27, 31, 30, 29, 28]
ORDER31 = [31, 30, 29, 28, 24, 25, 26, 27, 23, 22, 21, 20, 16, 17, 18, 19, 15, 14, 13, 12, 8, 9, 10, 11, 7, 6, 5, 4, 0, 1, 2, 3]

BASE = dict(P_W=5.0, P_W0=11.5, G_W=1.2, G_W0=5.3, PH_W=1.15, PH_W0=1.5, CAP=9, MINV=11,
            GOAL=GOAL0, ANY_STOP=False, STOP_AT=None, WFACT=6.25, WLEFT=6.0, PHW_LIST=None,
            NO15_LATE=2.0, LATE14=True, ORDERED=False)


class C:
    __slots__ = ("o", "a", "x", "y", "b", "ox", "oy")
    K = 1.0                                     # moltiplicatore dei costi di codice (taratura)

    def __init__(s):
        s.o = 0
        s.a = 0
        s.x = 0
        s.y = 0

    def r(s, *a):
        t = (s.a + s.o * C.K,) + a
        s.o = 0
        s.a = 0
        return t


def go_to_k(c, k, cur):
    # call 1, 4 assegnazioni con un operatore = 4, 4 while (1 prima volta + 1 per valutazione)
    tx, ty, cx, cy = k % BW, k // BW, cur % BW, cur // BW
    m = abs(tx - cx) + abs(ty - cy)
    c.o += 1 + 4 + 4 + (m + 4) + m
    c.a += m * 200
    return k


def goto(c, tx, ty):
    dx = (tx - c.x) % S
    n = dx if dx <= S // 2 else S - dx
    c.o += 3 + 3 + 1 + n
    c.a += n * 200          # get_pos_x, -, %; if <=, //; range; for+move
    dy = (ty - c.y) % S
    n2 = dy if dy <= S // 2 else S - dy
    c.o += 3 + 3 + 1 + n2 + 1
    c.a += n2 * 200     # + chiamata
    c.x, c.y = tx, ty


def cell(c, k):
    return (c.oy + k // BW) * S + c.ox + k % BW


def plant_cell(c, P, k, deadline, th, cnt):
    MINV, CAP = P['MINV'], P['CAP']
    c.o += 1                                    # chiamata
    v = yield c.r('plant', cell(c, k))
    c.o += 1                                    # measure
    c.o += 1                                    # while (prima valutazione)
    while True:
        t = yield c.r('time')
        c.o += 1                                # get_time() < deadline
        if not t < deadline:
            break
        # bad(v, th, cnt)
        c.o += 1 + 2                            # chiamata, if v < MINV
        if v < MINV:
            b = True
        else:
            c.o += 4                            # if cnt[v-MINV] >= CAP
            if cnt[v - MINV] >= CAP:
                b = True
            else:
                c.o += 2                        # if v == 15
                b = False
                if v == 15:
                    t = yield c.r('time')
                    c.o += 2                    # th - get_time() < 2.0
                    b = th - t < P['NO15_LATE']
        if not b:
            break
        yield c.r('harv', cell(c, k))
        v = yield c.r('plant', cell(c, k))
        c.o += 1
    c.o += 1                                    # while v >= 14 and get_time() >= deadline
    while P['LATE14']:
        c.o += 1
        if not v >= 14:
            break
        t = yield c.r('time')
        c.o += 1
        if not t >= deadline:
            break
        yield c.r('harv', cell(c, k))
        v = yield c.r('plant', cell(c, k))
        c.o += 1
    t = yield c.r('time')
    left = th + (15 - v) * P['PH_W'] - t
    c.o += 4 + 2                                # left = ..., if left < 6.0
    if left < P['WLEFT']:
        w = yield c.r('getw', cell(c, k))
        x = P['WFACT'] / left - 1 - 4 * w
        c.o += 4 + 1 + 2                        # x = ..., add = x // 1, if add < x
        add = x // 1
        if add < x:
            add += 1
            c.o += 1
        c.o += 2
        if add > 4:
            add = 4
        c.o += 2
        if add > 0:
            ok = yield c.r('water', cell(c, k), int(add))
            c.o += 1
            if not ok:
                c.o += 2
                if add > 1:
                    yield c.r('water', cell(c, k), 1)
    c.o += 2
    if v >= MINV:
        cnt[v - MINV] += 1
        c.o += 3
    return v


def plant_sweep(c, P, vals, cur, first, deadline, th, grass):
    MINV = P['MINV']
    cnt = [0] * (16 - MINV)
    c.o += 1 + 5 + 2 + 32                       # chiamata, cnt, if cur == 0, order
    order = ORDER0 if cur == 0 else ORDER31
    for k in order:
        c.o += 1
        cur = go_to_k(c, k, cur)
        if first:
            c.o += 1 + 3                        # if first, get_ground_type != SOIL
            if not grass[k]:
                pass
            c.a += 200                          # till (erba -> terra, toglie l'erba)
            grass[k] = False
        c.o += 1 + 2                            # get_entity_type, if t == SUN
        # nello script v5 una cella SUN con vals>=MINV non esiste piu' a inizio finestra
        has = vals[k] != 0
        if has and vals[k] >= MINV:
            c.o += 2
            cnt[vals[k] - MINV] += 1
            c.o += 3
        else:
            c.o += 2                            # if t != None
            if has:
                yield c.r('harv', cell(c, k))
            c.o += 2                            # chiamata + indice
            vals[k] = yield from plant_cell(c, P, k, deadline, th, cnt)
    return cur


def harvest_phase(c, P, vals, cur, v, main, stop):
    c.o += 1 + 1                                # chiamata, todo = []
    todo = [k for k in range(32) if vals[k] == v]
    c.o += 1 + 32 * 4 + len(todo)               # for + confronti + append
    cx, cy = cur % BW, cur // BW
    c.o += 2 + 1                                # cx, cy, while
    while True:
        c.o += 2                                # len(todo) > 0
        if not todo:
            break
        best, bd = 0, 99
        c.o += 1                                # while j < len(todo) (prima)
        for j, k in enumerate(todo):
            c.o += 2 + 1 + 7 + 2 + 1
            d = abs(k % BW - cx) + abs(k // BW - cy)
            if d < bd:
                bd, best = d, j
        c.o += 2                                # ultima valutazione falsa
        k = todo.pop(best)
        c.o += 1
        cur = go_to_k(c, k, cur)
        cx, cy = k % BW, k // BW
        c.o += 2
        yield c.r('harv', cell(c, k))
        vals[k] = 0
        c.o += 1 + 1                            # vals[k] = 0, if main
        if main or stop:
            p = yield c.r('num')
            c.o += 1
            if p >= P['STOP_AT']:
                return -1
    return cur


def run(c, P, b, t0, main):
    MINV = P['MINV']
    c.b = b
    c.ox, c.oy = BW * (b % 8), BH * (b // 8)
    goto(c, c.ox, c.oy)
    vals = [0] * 32
    grass = [True] * 32
    c.o += 1 + 1 + 32 * 2 + 4                   # vals, for+append, cur, t, r
    cur = 0
    t = t0
    r = 0
    stop = P['ANY_STOP']
    phl = P['PHW_LIST']
    c.o += 1                                    # while True
    while True:
        c.o += 2
        if r == 0:
            pw, gw = P['P_W0'], P['G_W0']
        else:
            pw, gw = P['P_W'], P['G_W']
        th = t + pw + gw
        c.o += 2 + 4
        if cur // BW < BH // 2:
            cur = go_to_k(c, 0, cur)
        else:
            cur = go_to_k(c, 31, cur)
        c.o += 3
        cur = yield from plant_sweep(c, P, vals, cur, r == 0, t + pw, th, grass)
        c.o += 1 + 2                            # if main, wait_until chiamata
        if main:
            yield c.r('trace', ('plant', r, t + pw))
        yield c.r('wait', th)
        v = 15
        c.o += 1
        i = 0
        while True:
            c.o += 1
            if not v >= MINV:
                break
            c.o += 1
            cur = yield from harvest_phase(c, P, vals, cur, v, main, stop)
            c.o += 2
            if cur < 0:
                yield c.r('clear')
                return
            if main:
                yield c.r('trace', ('fase', v, th + P['PH_W']))
            c.o += 1 + 3
            if r == 0 and i == 0:
                th += P['PH_W0']
            elif phl is not None:
                th += phl[i]
            else:
                th += P['PH_W']
            c.o += 1 + 2
            yield c.r('wait', th)
            i += 1
            c.o += 1
        t = th
        r += 1
        c.o += 1


def spawn_range(c, P, lo, hi, t0):
    c.o += 1 + 1
    while True:
        c.o += 2
        if not hi - lo > 1:
            break
        mid = (lo + hi) // 2
        c.o += 2 + 1 + 1
        yield c.r('spawn', task(P, mid, hi, t0))
        hi = mid
    yield from run(c, P, lo, t0, False)


def task(P, lo, hi, t0):
    def mk(d):
        c = C()
        return spawn_range(c, P, lo, hi, t0)
    return mk


def main_prog(d, P, main):
    c = C()
    c.o += 0
    yield c.r('clear0')  if False else c.r('time')   # clear() iniziale: vedi sotto
    c.a += 200                                  # clear()
    t0 = yield c.r('time')
    c.o += 1 + 1
    yield c.r('spawn', task(P, 1, 32, t0))
    yield from run(c, P, 0, t0, True)


def sim(P, seed):
    Q = dict(BASE)
    Q.update(P)
    g = _goal(Q, seed)
    Q['STOP_AT'] = g + (Q['STOP_AT'] - GOAL0 if Q['STOP_AT'] is not None else 0)
    return _scale(simulate(main_prog, Q, seed, goal=g), g)


# ===========================================================================
# v7: liste per valore costruite nella finestra (ordine della serpentina), fasi senza
# scansione dei 32 valori ne' giro greedy; stop da qualunque drone con margine.
# ===========================================================================

def plant_sweep7(c, P, lst, cur, first, deadline, th, grass, has):
    MINV = P['MINV']
    c.o += 1 + 2 + 32                           # chiamata, if cur == 0, order
    order = ORDER0 if cur == 0 else ORDER31
    skip = P.get('SKIP')
    for k in order:
        c.o += 1
        if skip is not None and not first:
            # v7: se manca troppo poco a th smetti di piantare (celle vuote)
            tn = yield c.r('time')
            c.o += 3
            if tn >= th - skip:
                break
        if P.get('FIXDIR'):
            # serpentina con direzioni fisse: 'if i > 0: move(DIRS[i - 1])' invece di go_to_k
            c.o += 2                            # if i > 0
            if k != order[0]:
                c.o += 2                        # indice DIRS[i - 1]
                c.a += 200
            cur = k
        else:
            cur = go_to_k(c, k, cur)
        if first:
            c.o += 1 + 3
            c.a += 200
        c.o += 1 + 2                            # get_entity_type() != None
        if has[k]:
            yield c.r('harv', cell(c, k))
        c.o += 1                                # chiamata
        v = yield from plant_cell7(c, P, k, deadline, th, lst)
        c.o += 2
        if v >= MINV:
            lst[v - MINV].append(k)
            c.o += 3
            has[k] = False                      # verra' raccolta nella sua fase
        else:
            has[k] = True
    return cur


def plant_cell7(c, P, k, deadline, th, lst):
    # come plant_cell ma il CAP usa len(lst[v-MINV]) (stessi costi) e niente cnt
    MINV, CAP = P['MINV'], P['CAP']
    v = yield c.r('plant', cell(c, k))
    c.o += 1 + 1
    while True:
        t = yield c.r('time')
        c.o += 1
        if not t < deadline:
            break
        c.o += 1 + 2
        if v < MINV:
            b = True
        else:
            c.o += 5                            # len(lst[v-MINV]) >= CAP
            if len(lst[v - MINV]) >= CAP:
                b = True
            else:
                c.o += 2
                b = False
                if v == 15:
                    t = yield c.r('time')
                    c.o += 2
                    b = th - t < P['NO15_LATE']
        if not b:
            break
        yield c.r('harv', cell(c, k))
        v = yield c.r('plant', cell(c, k))
        c.o += 1
    c.o += 1
    while P['LATE14']:
        c.o += 1
        if not v >= 14:
            break
        t = yield c.r('time')
        c.o += 1
        if not t >= deadline:
            break
        yield c.r('harv', cell(c, k))
        v = yield c.r('plant', cell(c, k))
        c.o += 1
    if v >= MINV:
        t = yield c.r('time')
        phl = P['PHW_LIST']
        if P.get('GROUPS'):
            gi = [j for j, g in enumerate(P['GROUPS']) if v in g][0]
            ahead = gi * P['PH_W'] if phl is None else sum(phl[:gi])
        else:
            ahead = (15 - v) * P['PH_W'] if phl is None else sum(phl[:15 - v])
        left = th + ahead - t
        c.o += 2 + 4 + 2
        if left < P['WLEFT']:
            w = yield c.r('getw', cell(c, k))
            x = P['WFACT'] / left - 1 - 4 * w
            c.o += 4 + 1 + 2
            add = x // 1
            if add < x:
                add += 1
                c.o += 1
            if P.get('FILL') and add > 0:
                add = int((1 - w) * 4 + 0.999)
                c.o += 4
            c.o += 2
            if add > 4:
                add = 4
            c.o += 2
            if add > 0:
                ok = yield c.r('water', cell(c, k), int(add))
                c.o += 1
                if not ok:
                    c.o += 2
                    if add > 1:
                        yield c.r('water', cell(c, k), 1)
    return v


def harvest_phase7(c, P, L, cur, stop, tend=None, v=None, lst=None, has=None):
    c.o += 1 + 1 + 2                            # chiamata, n = len(L), if n == 0
    n = len(L)
    if n == 0:
        return cur
    a, b = L[0], L[-1]
    cx, cy = cur % BW, cur // BW
    da = abs(a % BW - cx) + abs(a // BW - cy)
    db = abs(b % BW - cx) + abs(b // BW - cy)
    c.o += 2 + 2 + 7 + 7 + 2                    # a, b, cx, cy, da, db, if
    seq = L if da <= db else L[::-1]
    c.o += 1 if da <= db else 2
    for k in seq:
        c.o += 1 if da <= db else 3             # for / (while + indice + i -= 1)
        a0 = c.a
        cur = go_to_k(c, k, cur)
        if P.get('PHMOVEX') is not None:
            c.a = a0 + (c.a - a0) * P['PHMOVEX']   # solo test: limite superiore
        yield c.r('harv', cell(c, k))
        if stop:
            c.o += 1 + 1
            p = yield c.r('num')
            if p >= P['STOP_AT']:
                return -1
        cm = P.get('CASC_MIN')
        if cm is not None and v is not None and v >= cm:
            # cascata: ripianta subito; tieni u in [MINV, v-GAP] (annaffiata, raccolta in
            # questo round alla fase u), lascia u < MINV (innocuo), togli u > v-GAP
            tn = yield c.r('time')
            c.o += 4
            if tn < tend - P.get('CASC_M', 0.1):
                u = yield c.r('plant', cell(c, k))
                c.o += 1 + 4
                if P['MINV'] <= u <= v - P.get('CASC_GAP', 2):
                    yield c.r('water', cell(c, k), P.get('CASC_W', 4))
                    lst[u - P['MINV']].append(k)
                    c.o += 4
                elif u < P['MINV']:
                    has[k] = True
                    c.o += 2
                else:
                    yield c.r('harv', cell(c, k))
                    c.o += 2
        if P.get('PHWATER') is not None and tend is not None:
            # v9: annaffia la cella appena raccolta se la fase ha ancora tempo (l'acqua resta
            # nella cella e serve alla semina del round dopo)
            tn = yield c.r('time')
            c.o += 3
            if tn < tend - P['PHWATER']:
                w = yield c.r('getw', cell(c, k))
                add = int((P.get('PHFILL', 1.0) - w) * 4 + 0.999)
                c.o += 6
                if add > 0:
                    yield c.r('water', cell(c, k), min(add, 4))
    del L[:]
    c.o += 1                                    # svuota la lista (L = [] nel chiamante)
    return cur


def run7(c, P, b, t0, main):
    MINV = P['MINV']
    c.b = b
    c.ox, c.oy = BW * (b % 8), BH * (b // 8)
    goto(c, c.ox, c.oy)
    lst = [[] for _ in range(16 - MINV)]
    grass = [True] * 32
    has = [True] * 32                           # erba presente all'inizio
    c.o += 6 + 4
    cur, t, r = 0, t0, 0
    stop = P['ANY_STOP'] or main
    phl = P['PHW_LIST']
    c.o += 1
    while True:
        c.o += 2
        if r == 0:
            pw, gw = P['P_W0'], P['G_W0']
        else:
            pw, gw = P['P_W'], P['G_W']
            gl = P.get('G_LIST')
            if gl is not None and r - 1 < len(gl):
                gw = gl[r - 1]
        th = t + pw + gw
        c.o += 2 + 4
        cur = go_to_k(c, 0 if cur // BW < BH // 2 else 31, cur)
        c.o += 3
        if r == 0:
            has = [False] * 32                  # il till del primo giro toglie l'erba
        cur = yield from plant_sweep7(c, P, lst, cur, r == 0, t + pw, th, grass, has)
        if r == 0 and P.get('EARLY'):
            # round 0: finita la semina, raccogli i 15 gia' cresciuti per avere power prima
            L = lst[15 - MINV]
            while True:
                tn = yield c.r('time')
                c.o += 2
                if tn >= th - P['EARLY'] or not L:
                    break
                j = 0
                c.o += 1
                while j < len(L):
                    k = L[j]
                    cur = go_to_k(c, k, cur)
                    c.o += 4
                    ok = yield c.r('canh', cell(c, k))
                    if ok:
                        yield c.r('harv', cell(c, k))
                        L.pop(j)
                        c.o += 2
                        if stop:
                            p = yield c.r('num')
                    else:
                        j += 1
                        c.o += 1
                    tn = yield c.r('time')
                    if tn >= th - P['EARLY']:
                        break
        c.o += 1 + 2
        if main:
            yield c.r('trace', ('plant', r, t + pw))
        yield c.r('wait', th)
        groups = P.get('GROUPS') or [[x] for x in range(15, MINV - 1, -1)]
        v = 15
        i = 0
        c.o += 1
        while True:
            c.o += 1
            if not i < len(groups):
                break
            v = groups[i][0]
            c.o += 1 + 2
            tend = th + (P['PH_W0'] if (r == 0 and i == 0) else (phl[i] if phl is not None else P['PH_W']))
            for vv in groups[i]:
                c.o += 3
                cur = yield from harvest_phase7(c, P, lst[vv - MINV], cur, stop, tend, vv, lst, has)
                if cur < 0:
                    break
            c.o += 2
            if cur < 0:
                yield c.r('clear')
                return
            if main:
                yield c.r('trace', ('fase', v, th))
            c.o += 1 + 3
            if r == 0 and i == 0:
                th += P['PH_W0']
            elif phl is not None:
                th += phl[i]
            else:
                th += P['PH_W']
            c.o += 1 + 2
            yield c.r('wait', th)
            i += 1
            c.o += 1
        t = th
        r += 1
        c.o += 1


def spawn_range7(c, P, lo, hi, t0):
    c.o += 1 + 1
    while True:
        c.o += 2
        if not hi - lo > 1:
            break
        mid = (lo + hi) // 2
        c.o += 2 + 1 + 1
        yield c.r('spawn', task7(P, mid, hi, t0))
        hi = mid
    yield from run7(c, P, lo, t0, False)


def task7(P, lo, hi, t0):
    def mk(d):
        return spawn_range7(C(), P, lo, hi, t0)
    return mk


def main_prog7(d, P, main):
    c = C()
    yield c.r('time')
    if not P.get('NOCLEAR0'):
        c.a += 200
    t0 = yield c.r('time')
    c.o += 2
    yield c.r('spawn', task7(P, 1, 32, t0))
    yield from run7(c, P, 0, t0, True)


def sim7(P, seed):
    Q = dict(BASE)
    Q.update(dict(ANY_STOP=True, STOP_AT=GOAL0 + 10))
    Q.update(P)
    g = _goal(Q, seed)
    Q['STOP_AT'] = g + (Q['STOP_AT'] - GOAL0)
    return _scale(simulate(main_prog7, Q, seed, goal=g), g)


def _goal(Q, seed):
    # RANDGOAL: obiettivo casuale U[0.9,1.1]*GOAL per seed, per mediare l'allineamento
    # del superamento dentro l'ultimo round; il tempo viene riscalato a 100.000.
    if Q.get('RANDGOAL'):
        import random as _r
        return int(GOAL0 * (0.9 + 0.2 * _r.Random(seed * 7 + 3).random()))
    return GOAL0


def _scale(r, g):
    r['t_raw'] = r['t']
    if g != GOAL0:
        r['t'] = r['t'] * GOAL0 / g
    return r
