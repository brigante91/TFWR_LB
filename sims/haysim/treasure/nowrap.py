import random, statistics as st
from collections import deque
from pathgen import gen_path, levels
def run(path, wrap):
    S=8; lv=levels(path); zs=sorted(lv); cur=(path[1][0],path[1][1]); tot=0; exp=0; goal=(path[-1][0],path[-1][1])
    for zi,z in enumerate(zs[:-1]):
        cells=lv[z]; nxt=lv[zs[zi+1]] if zi<len(zs)-2 else {goal}
        d={cur:0}; q=deque([cur]); f=None
        while q:
            c=q.popleft(); exp+=1
            if c in nxt: f=c; break
            if wrap: ns=[((c[0]+1)%S,c[1]),((c[0]-1)%S,c[1]),(c[0],(c[1]+1)%S),(c[0],(c[1]-1)%S)]
            else: ns=[(c[0]+1,c[1]),(c[0]-1,c[1]),(c[0],c[1]+1),(c[0],c[1]-1)]
            for n in ns:
                if n in cells and n not in d: d[n]=d[c]+1; q.append(n)
        tot+=d[f]; cur=f
    return tot,exp
r=random.Random(11); A=[];B=[];EA=[];EB=[]
for _ in range(3000):
    p=gen_path(r,start=(r.randrange(2,6),r.randrange(2,6),0))
    a,ea=run(p,True); b,eb=run(p,False); A.append(a);B.append(b);EA.append(ea);EB.append(eb)
print("con wrap",st.mean(A),st.mean(EA)," senza",st.mean(B),st.mean(EB))
