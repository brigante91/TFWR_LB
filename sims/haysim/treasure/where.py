import random, statistics as st, heapq
from collections import deque
from pathgen import gen_path, levels
S=8
def nbs(c): return [((c[0]+1)%S,c[1]),((c[0]-1)%S,c[1]),(c[0],(c[1]+1)%S),(c[0],(c[1]-1)%S)]
def bfs(cells, src):
    d={src:0}; q=deque([src])
    while q:
        c=q.popleft()
        for n in nbs(c):
            if n in cells and n not in d: d[n]=d[c]+1; q.append(n)
    return d
def plan(path, k_opt):
    # livelli 1..8; ultimi k_opt livelli pianificati all'indietro (ottimo), prima avido
    lv=levels(path); zs=sorted(lv); goal=(path[-1][0],path[-1][1])
    L=[lv[z] for z in zs[:-1]]  # 8 livelli
    # costo all'indietro: cost[i][c] = mosse minime da c (livello i) alla fine
    cost=[None]*len(L); nxt={goal:0}
    for i in range(len(L)-1,-1,-1):
        cells=L[i]; d={}; h=[]
        for c,v in nxt.items():
            if c in cells: d[c]=v; h.append((v,c))
        heapq.heapify(h)
        while h:
            v,c=heapq.heappop(h)
            if v>d[c]: continue
            for n in nbs(c):
                if n in cells and d.get(n,1e9)>v+1: d[n]=v+1; heapq.heappush(h,(v+1,n))
        cost[i]=d; nxt=d
    cur=(path[1][0],path[1][1]); tot=0; n=len(L)
    for i in range(n):
        nxtset=L[i+1] if i+1<n else {goal}
        d=bfs(L[i],cur)
        if i>=n-k_opt:
            # scegli candidato che minimizza d + costo futuro
            best=min((d[c]+cost[i+1][c] if i+1<n else d[c], c) for c in d if c in nxtset)
            # con ottimo: segue cost
            c=best[1]
        else:
            c=min((d[c],c) for c in d if c in nxtset)[1]
        tot+=d[c]; cur=c
    return tot
r=random.Random(5); R={k:[] for k in (0,1,2,3,8)}
for _ in range(2000):
    p=gen_path(r,start=(r.randrange(2,6),r.randrange(2,6),0))
    for k in R: R[k].append(plan(p,k))
for k in R: print("ultimi",k,"livelli ottimi:",round(st.mean(R[k]),2))
