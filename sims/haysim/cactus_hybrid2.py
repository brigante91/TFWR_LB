import random, statistics
from cactus_sort_sim import shaker  # stessa cartella
S=32
def sorted_cell(g, x, y):
    v=g[x][y]
    def ok(one,two):  # one <= two richiesto (one sotto/sinistra, two sopra/destra)
        return one is None or two is None or one <= two
    n = g[x][y+1] if y+1<S else None
    e = g[x+1][y] if x+1<S else None
    s = g[x][y-1] if y>0 else None
    w = g[x-1][y] if x>0 else None
    return ok(v,n) and ok(v,e) and ok(s,v) and ok(w,v)
def pop_risk(g,x,y):
    # pop si propaga se TUTTI i vicini cactus sono sorted
    for (nx,ny) in ((x,y+1),(x+1,y),(x,y-1),(x-1,y)):
        if 0<=nx<S and 0<=ny<S and not sorted_cell(g,nx,ny):
            return False
    return True
def run(K, slack, till_from, trials=200):
    tot=[]; pops=[0]*(K+1); harv=[0]*(K+1)
    for _ in range(trials):
        g=[[random.randrange(10) for y in range(S)] for x in range(S)]
        col=[]
        for x in range(S):
            acts=2*S
            for k in range(K):
                bad=0; risk=0
                for y in range(S):
                    t=((x+y)*10)//(2*S-1)
                    if abs(g[x][y]-t)>slack:
                        if k < till_from:  # harvest+plant
                            harv[k]+=1
                            if pop_risk(g,x,y): pops[k]+=1
                            acts+=2
                        else:
                            acts+=3
                        g[x][y]=random.randrange(10); bad+=1
                acts+=S
                if bad==0: break
            acts+=shaker(g[x]); col.append(acts)
        rows=[shaker([g[x][y] for x in range(S)]) for y in range(S)]
        tot.append((max(col)+max(rows))*200/6075)
    return statistics.mean(tot), [ (pops[k], harv[k]) for k in range(K) ]
random.seed(3)
for K in (0,2,3,4,6,8):
    for tf in (0,1,2,K):
        if tf>K: continue
        m, pr = run(K,1,tf)
        print(f"K={K} harvest-reroll nei primi {tf} giri: {m:5.1f} s   pop/harvest per giro: {[(p,h) for p,h in pr]}")
