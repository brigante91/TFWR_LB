# distribuzione del lavoro per fase (mosse + raccolti) con l'ordine a serpentina e col giro ottimo
import random, itertools, statistics as S
BW, BH = 4, 8
ORDER0 = [0, 1, 2, 3, 7, 6, 5, 4, 8, 9, 10, 11, 15, 14, 13, 12, 16, 17, 18, 19, 23, 22, 21, 20, 24, 25, 26, 27, 31, 30, 29, 28]
def dist(a, b): return abs(a % BW - b % BW) + abs(a // BW - b // BW)
def serp_len(L, cur):
    if not L: return 0, cur
    if dist(L[0], cur) <= dist(L[-1], cur): seq = L
    else: seq = L[::-1]
    m = 0
    for k in seq:
        m += dist(k, cur); cur = k
    return m, cur
def opt_len(L, cur, nxt=None):
    # percorso ottimo (aperto) partendo da cur
    if not L: return 0, cur
    best = None
    for p in itertools.permutations(L):
        m = 0; c = cur
        for k in p:
            m += dist(k, c); c = k
        if best is None or m < best[0]: best = (m, c)
    return best
rng = random.Random(1)
ws, wo, wo2 = [], [], []
for trial in range(3000):
    lst = {v: [] for v in range(9, 16)}
    order = ORDER0 if trial % 2 == 0 else ORDER0[::-1]
    for k in order:
        while True:
            v = rng.randint(7, 15)
            if v >= 9 and len(lst[v]) < 6: break
        lst[v].append(k)
    cur = order[-1]; cur2 = cur
    for v in range(15, 8, -1):
        m, cur = serp_len(lst[v], cur)
        ws.append(m * 200 + len(lst[v]) * 215)
        m2, cur2n = opt_len(lst[v], cur2)
        wo.append(m2 * 200 + len(lst[v]) * 215)
        # con pre-posizionamento: il primo tratto e' fuori dalla finestra
        first = min(dist(k, cur2) for k in lst[v]) if lst[v] else 0
        wo2.append((m2 - first) * 200 + len(lst[v]) * 215)
        cur2 = cur2n
def q(x, p): x = sorted(x); return x[int(p * (len(x) - 1))]
for name, x in (('serpentina', ws), ('ottimo', wo), ('ottimo+prepos (limite inf.)', wo2)):
    print(name, 'media', S.mean(x), 'p90', q(x, .9), 'p99', q(x, .99), 'p999', q(x, .999), 'max', max(x), ' s:', q(x, .999) / 6075)
