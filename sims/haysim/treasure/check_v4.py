# verifica di route/walk della v4 su percorsi generati: ogni cella visitata deve essere nel percorso
import random, re
from pathgen import gen_path
src = open('../../lb_treasure.py').read()
a = src.index('def walk'); b = src.index('n_tes = 0')
East, West, North, South = 'E', 'W', 'N', 'S'
DL = {"E": 1, "W": -1, "N": 10, "S": -10, "D": 100}
DIRD = {1: East, -1: West, 10: North, -10: South}
pos = [0]; trail = []
def move(d): pos[0] += DL[d]; trail.append(pos[0])
exec(src[a:b])
def tostr(path):
    out = []
    for p, q in zip(path, path[1:]):
        d = (q[0]-p[0], q[1]-p[1], q[2]-p[2])
        out.append({(1,0,0):'E',(-1,0,0):'W',(0,1,0):'N',(0,-1,0):'S',(0,0,1):'D'}[d])
    return ''.join(out)
r = random.Random(3); bad = 0; mv = 0; N = 2000
for _ in range(N):
    m = (r.randrange(2,6), r.randrange(2,6))
    p = gen_path(r, start=(m[0], m[1], 0)); s = tostr(p)
    q = m[1]*10 + m[0]; S = {}
    for c in s: q += DL[c]; S[q] = 1
    goal = q
    q = m[1]*10 + m[0] + 100; pos[0] = q; trail.clear()
    while q != goal:
        if q + 100 not in S:
            q = route(S, q)
        if pos[0] != q or q not in S: bad += 1; break
        q += 100; pos[0] = q
        if q not in S: bad += 1; break
    bad += sum(1 for t in trail if t not in S)
    mv += len(trail)
print("errori", bad, "mosse medie", mv / N)
