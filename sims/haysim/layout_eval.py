"""Valuta layout per carote/alberi: costo per raccolto = 400 (harvest+plant) + 403*(1/acc-1) (reroll)
+ 200*mosse/raccolto + attesa crescita. acc = (1/3) * (celle del rombo r=3 che NON sono carote)/24."""
import itertools
S=32
DIAMOND=[(dx,dy) for dx in range(-3,4) for dy in range(-3,4) if (dx or dy) and abs(dx)+abs(dy)<=3]
GROW=7290  # carota 6 s / 5 con acqua 1.0 (media)
def evaluate(drones, grow=GROW, extra=50):
    """drones: lista di tour (lista di celle in ordine ciclico). Ritorna costo medio per raccolto."""
    cells=set(c for t in drones for c in t)
    tot=0; n=0; per=[]
    for tour in drones:
        k=len(tour)
        moves=sum(min(abs(a[0]-b[0]),S-abs(a[0]-b[0]))+min(abs(a[1]-b[1]),S-abs(a[1]-b[1])) for a,b in zip(tour,tour[1:]+tour[:1]))
        cost=0
        for c in tour:
            free=sum(1 for dx,dy in DIAMOND if ((c[0]+dx)%S,(c[1]+dy)%S) not in cells)
            acc=free/24/3
            cost+=400+403*(1/acc-1)+extra
        cost+=200*moves
        lap=cost  # tick per giro
        if lap<grow: lap=grow  # il drone aspetta la crescita
        per.append(lap/k)
    return sum(per)/len(per), max(per), len(cells)

def ring_block(x0,y0,w,h):
    # perimetro di un blocco w x h (w,h>=2) in ordine ciclico (tutte le celle se h==2 o w==2)
    cells=[(x0+i,y0+j) for i in range(w) for j in range(h)]
    if h==2:
        return [(x0+i,y0) for i in range(w)]+[(x0+w-1-i,y0+1) for i in range(w)]
    if w==2:
        return [(x0,y0+j) for j in range(h)]+[(x0+1,y0+h-1-j) for j in range(h)]
    return cells

def layout_blocks(w,h,px,py,need=32):
    nx=S//px; ny=S//py
    drones=[]
    for j in range(ny):
        for i in range(nx):
            drones.append([((x)%S,(y)%S) for x,y in ring_block(i*px,j*py,w,h)])
    return drones[:need] if len(drones)>=need else None

print("wood_best (6 coppie di righe, anelli da 6):")
ROWS=[0,3,6,8,11,14,16,19,22,24,27,30]
tours=[]
for pi in range(6):
    ya,yb=ROWS[2*pi],ROWS[2*pi+1]
    for L in range(5):
        x0=6*L
        tours.append([(x0+2*j,ya) for j in range(3)]+[(x0+1+2*j,yb) for j in reversed(range(3))])
rest=[(30 if i%2==0 else 31,y) for i,y in enumerate(ROWS)]
tours.append(rest[:6]); tours.append(rest[6:])
print("  medio %.0f  max %.0f  celle %d" % evaluate(tours))

best=[]
for (w,h) in [(2,2),(2,3),(3,2),(2,4),(4,2),(3,3),(2,5),(2,6),(3,4)]:
    for px in range(w+1,9):
        for py in range(h+1,12):
            d=layout_blocks(w,h,px,py)
            if d is None: continue
            m,mx,nc=evaluate(d)
            best.append((m,mx,w,h,px,py,nc))
best.sort()
for b in best[:15]:
    print("  blocco %dx%d passo (%d,%d): medio %.0f max %.0f celle %d" % (b[2],b[3],b[4],b[5],b[0],b[1],b[6]))
