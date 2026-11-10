"""Confronto algoritmi di ordinamento per un drone su una linea di 32 cactus (valori 0..9).
Costo = azioni da 200 tick (move, swap). measure costa 1 e si ignora."""
import random, statistics

def inversions(a):
    return sum(1 for i in range(len(a)) for j in range(i+1,len(a)) if a[i]>a[j])

def shaker(a):
    a=a[:]; n=len(a); lo=0; hi=n-1; pos=0; acts=0
    while lo<hi:
        last=lo
        for k in range(lo,hi):
            if a[k]>a[k+1]: a[k],a[k+1]=a[k+1],a[k]; last=k; acts+=1
            acts+=1  # move fwd
        acts+= (hi-last); hi=last
        if lo>=hi: break
        last=hi
        for k in range(hi,lo,-1):
            if a[k-1]>a[k]: a[k-1],a[k]=a[k],a[k-1]; last=k; acts+=1
            acts+=1
        acts+= (last-lo); lo=last
    return acts

def insertion_carry(a):
    # il drone parte da 0; per k=1..n-1: va a k (gia' li'), porta a[k] indietro finche' serve, poi torna avanti
    a=a[:]; n=len(a); acts=0
    for k in range(1,n):
        acts+=1  # move a k
        j=k
        while j>0 and a[j-1]>a[j]:
            a[j-1],a[j]=a[j],a[j-1]; acts+=1  # swap(back)
            acts+=1  # move back
            j-=1
        acts+= (k-j)  # ritorno a k
    return acts

def insertion_carry_fwd_only(a):
    # variante: al ritorno non si torna a k ma si continua da j: l'elemento successivo va raccolto...
    # equivalente a gnome sort: dopo ogni swap-back si deve risalire. Uguale a insertion_carry.
    return insertion_carry(a)

def shaker_carry(a):
    """Shaker in cui nella passata avanti il drone porta con se' il massimo e in quella indietro il minimo
    (e' lo shaker classico: gia' lo fa). Alternativa: bubble solo avanti con rientro via wrap (torus!)."""
    a=a[:]; n=len(a); hi=n-1; acts=0; lo=0
    while lo<hi:
        last=lo
        for k in range(lo,hi):
            if a[k]>a[k+1]: a[k],a[k+1]=a[k+1],a[k]; last=k; acts+=1
            acts+=1
        hi=last
        # rientro via wrap del mondo: da hi a lo costa min(hi-lo, n-(hi-lo))
        d=hi-lo; acts+=min(d, n-d)
    return acts

def optimal_lower(a):
    return inversions(a)

random.seed(1)
N=4000
res={k:[] for k in ['inv','shaker','insertion','bubble_wrap']}
for _ in range(N):
    a=[random.randrange(10) for _ in range(32)]
    res['inv'].append(inversions(a))
    res['shaker'].append(shaker(a))
    res['insertion'].append(insertion_carry(a))
    res['bubble_wrap'].append(shaker_carry(a))
for k,v in res.items():
    print(f"{k:12s} media {statistics.mean(v):7.1f} azioni  -> {statistics.mean(v)*200/6075:5.1f} s   (p95 {sorted(v)[int(0.95*N)]})")

# fase righe: dopo l'ordinamento delle colonne, le righe sono statistiche d'ordine
rows_sh=[]; rows_inv=[]
for _ in range(500):
    grid=[sorted(random.randrange(10) for _ in range(32)) for _ in range(32)]  # grid[x][y]
    tot=0; ti=0
    for y in range(32):
        row=[grid[x][y] for x in range(32)]
        tot+=shaker(row); ti+=inversions(row)
    rows_sh.append(tot/32); rows_inv.append(ti/32)
print(f"righe dopo colonne: inversioni medie {statistics.mean(rows_inv):.1f}, shaker {statistics.mean(rows_sh):.1f} azioni -> {statistics.mean(rows_sh)*200/6075:.1f} s")
