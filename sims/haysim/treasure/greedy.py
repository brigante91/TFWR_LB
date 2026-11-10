import random, statistics as st
from collections import deque
from pathgen import gen_path, levels, best3d
S=8
def nb(c): return [((c[0]+1)%S,c[1]),((c[0]-1)%S,c[1]),(c[0],(c[1]+1)%S),(c[0],(c[1]-1)%S)]
def greedy(path):
    lv=levels(path); zs=sorted(lv); cur=(path[1][0],path[1][1]); tot=0; bfsn=0
    for zi,z in enumerate(zs[:-1]):
        nxt=lv[zs[zi+1]]; cells=lv[z]
        if zi==len(zs)-2: nxt={(path[-1][0],path[-1][1])}
        d={cur:0}; q=deque([cur]); found=None
        while q:
            c=q.popleft(); bfsn+=1
            if c in nxt: found=c; break
            for n in nb(c):
                if n in cells and n not in d: d[n]=d[c]+1; q.append(n)
        tot+=d[found]; cur=found
    return tot,bfsn
r=random.Random(5); G=[];B=[];N=[]
for _ in range(2000):
    p=gen_path(r,start=(r.randrange(2,6),r.randrange(2,6),0))
    g,n=greedy(p); G.append(g); N.append(n); B.append(best3d(p))
print("avido",st.mean(G),"ottimo",st.mean(B),"nodi BFS espansi",st.mean(N))
