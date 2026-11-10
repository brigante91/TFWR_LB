# Porting di TreasureMapController.GeneratePath (8x8, profondita' 9)
import random, math
from collections import deque

def gen_path(r, S=8, depth=9, start=(0,0,0)):
    t = min(1, max(0, (S-4)/28))
    num = math.ceil(5 + (25-5)*t); num2 = math.ceil(10 + (5-10)*t)
    path = [start]
    def last(steps): return steps[-1] if steps else path[-1]
    def to_target(steps, target, first=-1):
        p = list(last(steps)); s = [int(math.copysign(1, target[i]-p[i])) if target[i]!=p[i] else 0 for i in range(2)]
        a = first if first in (0,1) else r.randrange(2)
        while p[a] != target[a]:
            p[a] += s[a]; steps.append(tuple(p))
        a = 1-a
        while p[a] != target[a]:
            p[a] += s[a]; steps.append(tuple(p))
    def rand_target(steps):
        p = last(steps); to_target(steps, (r.randrange(S), r.randrange(S), p[2]))
    def back_forth(steps):
        p = list(last(steps)); i = r.randrange(2); n = r.randrange(1, S//2+1)
        if p[i] < n: v = 1
        elif p[i] + n < S: v = 1 if r.randrange(2) != 0 else -1
        else: v = -1
        for _ in range(n): p[i] += v; steps.append(tuple(p))
        for _ in range(n): p[i] -= v; steps.append(tuple(p))
    def loop(steps):
        p = last(steps)
        sx = 1 if r.randrange(2) else -1  # RandomSign chiamato dopo Next(2, S/2)
        # ordine C#: Next(2,S/2) poi RandomSign per x, poi per y
        q = None
        return p
    def loop2(steps):
        p = last(steps)
        ax = 2 if S//2 <= 2 else r.randrange(2, S//2); sx = 1 if r.randrange(2) != 0 else -1
        ay = 2 if S//2 <= 2 else r.randrange(2, S//2); sy = 1 if r.randrange(2) != 0 else -1
        tgt = ((p[0]+ax*sx) % S, (p[1]+ay*sy) % S, p[2])
        first = r.randrange(2)
        to_target(steps, tgt, first); to_target(steps, p, first)
    def repeat_copy(gen, lo, hi):
        def g(steps):
            n = r.randint(lo, hi)
            if n > 0:
                c = len(steps); gen(steps); c2 = len(steps)
                seg = steps[c:c2]
                for _ in range(1, n): steps.extend(seg)
        return g
    def down(steps):
        p = last(steps); steps.append((p[0], p[1], p[2]+1))
    for i in range(1, depth):
        st = []; down(st); path.extend(st)
        k = r.randint(1, num)
        for _ in range(k):
            x = r.random(); st = []
            if x < 0.5: rand_target(st)
            elif x < 0.8: repeat_copy(back_forth, 1, num2//2)(st)
            else: repeat_copy(loop2, 1, num2)(st)
            path.extend(st)
    st = []; down(st); path.extend(st)
    return path

def shortcut_moves(path, S=8):
    # per livello: BFS sulle celle del percorso (con wrap) dall'ingresso alla cella del D
    tot = 0; per = []
    i = 1
    while i < len(path)-1:
        z = path[i][2]; j = i
        while path[j+1][2] == z: j += 1
        cells = set((p[0],p[1]) for p in path[i:j+1])
        s = (path[i][0], path[i][1]); g = (path[j][0], path[j][1])
        d = {s:0}; q = deque([s])
        while q:
            c = q.popleft()
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                n = ((c[0]+dx)%S, (c[1]+dy)%S)
                if n in cells and n not in d: d[n] = d[c]+1; q.append(n)
        per.append((d[g], j-i, len(cells)))
        tot += d[g]; i = j+1
    return tot, per

if __name__ == "__main__":
    import statistics as st
    r = random.Random(1)
    L=[]; M=[]; W=[]
    for _ in range(2000):
        p = gen_path(r, start=(r.randrange(2,6), r.randrange(2,6), 0))
        L.append(len(p)); m, per = shortcut_moves(p); M.append(m); W.append(sum(x[1] for x in per))
    print("lunghezza media", st.mean(L), "min", min(L), "max", max(L))
    print("mosse lungo il percorso", st.mean(W), " mosse con scorciatoie", st.mean(M))
    print("oro medio per tesoro", 16*st.mean(L), " tesori per 115000:", 115000/(16*st.mean(L)))

def levels(path):
    lv = {}
    for p in path[1:]:
        lv.setdefault(p[2], set()).add((p[0], p[1]))
    return lv

def best3d(path, S=8):
    lv = levels(path); zs = sorted(lv); goal = path[-1]
    # BFS a strati: distanza minima in mosse; dig gratis (sempre 8)
    start = (path[1][0], path[1][1])
    dist = {start: 0}
    for zi, z in enumerate(zs[:-1]):
        cells = lv[z]
        # BFS multi-sorgente su livello z
        q = sorted(dist, key=dist.get); d = dict(dist)
        dq = deque(q)
        # Dijkstra con pesi 1 = BFS con sorgenti a distanze diverse
        import heapq
        h = [(v, c) for c, v in d.items()]; heapq.heapify(h)
        while h:
            v, c = heapq.heappop(h)
            if v > d[c]: continue
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                n = ((c[0]+dx)%S, (c[1]+dy)%S)
                if n in cells and d.get(n, 1e9) > v+1: d[n] = v+1; heapq.heappush(h, (v+1, n))
        nxt = lv[zs[zi+1]]
        dist = {c: v for c, v in d.items() if c in nxt}
    return dist[(goal[0], goal[1])]

if __name__ == "__main__":
    r = random.Random(1); B=[]; M=[]
    for _ in range(2000):
        p = gen_path(r, start=(r.randrange(2,6), r.randrange(2,6), 0))
        B.append(best3d(p)); M.append(shortcut_moves(p)[0])
    print("mosse 2D", st.mean(M), " mosse 3D", st.mean(B), " distribuzione 3D", sorted(B)[::200])
