import random, statistics as st
from collections import deque
from pathgen import gen_path, best3d
from look import run as greedy
S=8
def code(p): return p[2]*64+p[1]*8+p[0]
def chain(path, nbcheck):
    # parse: N[p] = successore dell'ultima occorrenza; Sset celle
    Sset=set(); N={}
    for i in range(len(path)-1):
        a=code(path[i]); b=code(path[i+1]); N[a]=b; Sset.add(b)
    goal=code(path[-1]); q=code(path[1]); moves=0; ops=0
    def nb(q):
        z,p=divmod(q,64); x,y=p%8,p//8
        return [z*64+y*8+(x+1)%8, z*64+y*8+(x-1)%8, z*64+((y+1)%8)*8+x, z*64+((y-1)%8)*8+x]
    while q!=goal:
        if q+64 in Sset: q+=64; ops+=3; continue
        if nbcheck:
            hit=None
            for n in nb(q):
                ops+=4
                if n in Sset and n+64 in Sset: hit=n; break
            if hit is not None: q=hit; moves+=1; continue
        n=N[q]; ops+=4
        if n//64 != q//64: q=n; continue   # D nel percorso
        q=n; moves+=1
    return moves, ops
r=random.Random(11); G=[];C=[];C2=[];O1=[];O2=[]
for _ in range(3000):
    p=gen_path(r,start=(r.randrange(2,6),r.randrange(2,6),0))
    G.append(greedy(p,False)[0]); a,o=chain(p,False); b,o2=chain(p,True); C.append(a); C2.append(b); O1.append(o); O2.append(o2)
print("BFS avida",st.mean(G)," catena",st.mean(C),"op",st.mean(O1)," catena+vicini",st.mean(C2),"op",st.mean(O2))
