import random, statistics as st
from collections import deque
from pathgen import gen_path, levels, best3d
S=8
def nb(c): return [((c[0]+1)%S,c[1]),((c[0]-1)%S,c[1]),(c[0],(c[1]+1)%S),(c[0],(c[1]-1)%S)]
def run(path, look):
    lv=levels(path); zs=sorted(lv); cur=(path[1][0],path[1][1]); tot=0; exp=0
    goal=(path[-1][0],path[-1][1])
    for zi,z in enumerate(zs[:-1]):
        cells=lv[z]; nxt=lv[zs[zi+1]] if zi<len(zs)-2 else {goal}
        nn=lv[zs[zi+2]] if zi+2<len(zs) else set()
        if zi+2==len(zs)-1: nn={goal}
        d={cur:0}; q=deque([cur]); cand=[]; dmin=None
        while q:
            c=q.popleft(); exp+=1
            if dmin is not None and d[c]>dmin: break
            if c in nxt:
                if dmin is None: dmin=d[c]
                cand.append(c)
                if not look: break
                continue
            for n in nb(c):
                if n in cells and n not in d: d[n]=d[c]+1; q.append(n)
        best=cand[0]
        if look:
            for c in cand:
                if c in nn: best=c; break
        tot+=d[best]; cur=best
    return tot,exp
r=random.Random(7); A=[];B=[];O=[];E1=[];E2=[]
for _ in range(3000):
    p=gen_path(r,start=(r.randrange(2,6),r.randrange(2,6),0))
    a,e1=run(p,False); b,e2=run(p,True); A.append(a);B.append(b);O.append(best3d(p));E1.append(e1);E2.append(e2)
print("avido",st.mean(A),"lookahead",st.mean(B),"ottimo",st.mean(O),"espansioni",st.mean(E1),st.mean(E2))
