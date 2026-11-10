"""Genera rng_predictor/lb_sunflowers_v11.py dai parametri tarati (json di tune.py).
Uso: python3 gen_sun11.py best.json [uscita.py]
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

TEMPLATE = '''# Classifica Sunflowers: 100.000 power, 32 droni. v11 del 10 nov 2026 (dalla v10, 2:37.964).
# Stesso impianto (blocco 4x8 per drone, semina a serpentina, fasi sincronizzate con get_time dal
# valore 15 a MINV), con quattro modifiche misurate nel simulatore tarato (haysim/sun2/prog11.py,
# stesse regole di haysim/sunsim2.py):
# 1. Semina a ritmo: un rilancio si fa solo se il resto della serpentina sta ancora nella
#    finestra (tp - celle_rimaste * TAU); chi e' in ritardo non rilancia piu'.
# 2. Tetto di lavoro per fase: oltre a CAP celle per valore, il giro di ogni valore (mosse fra
#    le celle in ordine di semina * 200 + 215 a cella) non deve superare WB tick: la fase piu'
#    lunga si accorcia e la finestra PH_W scende da 0.85 a __PH_W__ s.
# 3. Rilancio dei semi che non farebbero in tempo a crescere: se alla fase del valore mancano
#    meno di LM[round] secondi (tanti nei primi round asciutti, pochi dopo) il seme si rilancia.
# 4. Attesa di crescita che cala coi round (GW): lunga finche' il campo e' asciutto, poi corta.
# Simulatore (16 semi, obiettivo 90-110k riscalato): v10 __T10__, v11 __T11__.
# Provate e scartate: spostarsi nel tempo morto sul capo della lista successiva, 15 raccolti nell'attesa di crescita, ripianto a cascata (anche con azioni
# allineate a un battito di tick), 8 o 9 livelli, attesa della crescita sulla cella.
#
# Regole: petali = Next(7,16) a ogni plant; bonus x8 se petali == massimo del campo (semi inclusi)
# e >= 10 girasoli; ogni harvest (anche di un seme) aggiorna il flag che toglie il bonus al
# raccolto successivo se l'ultimo non era un massimo; power iniziale 0 (meta' velocita').
GOAL = 100000
STOP = GOAL + 10   # margine contro il UsePower fra il controllo e la fine della run
MINV = __MINV__
CAP = __CAP__        # celle per valore per blocco
WB = __WB__      # tick: lavoro massimo del giro di un valore
P_W = __P_W__      # s: finestra di semina
P_W0 = __P_W0__    # s: primo round a meta' velocita'
G_W0 = __G_W0__     # s: primo round, crescita quasi secca
PH_W = __PH_W__    # s: fase di raccolta
PH_W0 = __PH_W0__    # s: prima fase del primo round (parte a velocita' dimezzata)
GW = __GW__   # s: attesa di crescita del round 1, 2, ...
G_INF = __G_INF__
LM = __LM__   # s: tempo minimo fra semina e fase, round 0, 1, ...
L_INF = __L_INF__
TAU = __TAU__    # s per cella rimasta: sotto questo margine niente rilanci
WF = __WF__       # acqua: 1+4w >= WF/L
WL = __WL__       # acqua solo se mancano meno di WL secondi alla fase

S = get_world_size()
SUN = Entities.Sunflower
SOIL = Grounds.Soil
WATER = Items.Water
POWER = Items.Power
BW = 4
BH = 8
ORDER0 = [0, 1, 2, 3, 7, 6, 5, 4, 8, 9, 10, 11, 15, 14, 13, 12, 16, 17, 18, 19, 23, 22, 21, 20, 24, 25, 26, 27, 31, 30, 29, 28]
ORDER31 = [31, 30, 29, 28, 24, 25, 26, 27, 23, 22, 21, 20, 16, 17, 18, 19, 15, 14, 13, 12, 8, 9, 10, 11, 7, 6, 5, 4, 0, 1, 2, 3]
DIRS0 = [East, East, East, North, West, West, West, North, East, East, East, North, West, West, West, North, East, East, East, North, West, West, West, North, East, East, East, North, West, West, West]
DIRS31 = [West, West, West, South, East, East, East, South, West, West, West, South, East, East, East, South, West, West, West, South, East, East, East, South, West, West, West, South, East, East, East]


def goto(tx, ty):
	dx = (tx - get_pos_x()) % S
	if dx <= S // 2:
		for _ in range(dx):
			move(East)
	else:
		for _ in range(S - dx):
			move(West)
	dy = (ty - get_pos_y()) % S
	if dy <= S // 2:
		for _ in range(dy):
			move(North)
	else:
		for _ in range(S - dy):
			move(South)


def wait_until(t):
	while get_time() < t:
		pass


def go_to_k(k, cur):
	# sposta il drone dalla cella cur alla cella k del blocco (coordinate relative)
	tx = k % BW
	ty = k // BW
	cx = cur % BW
	cy = cur // BW
	while cx < tx:
		move(East)
		cx += 1
	while cx > tx:
		move(West)
		cx -= 1
	while cy < ty:
		move(North)
		cy += 1
	while cy > ty:
		move(South)
		cy -= 1
	return k


def plant_cell(k, th, ex, lmin, tlim, lst, wk, last):
	# pianta la cella k; ritorna il valore tenuto (0 = cella lasciata vuota)
	plant(SUN)
	v = measure()
	du = 0
	while True:
		t = get_time()
		if v < MINV:
			kind = 1
		else:
			i = v - MINV
			# du = inizio della fase del valore v
			du = th + (15 - v) * PH_W
			if v < 15:
				du += ex
			n = len(lst[i])
			if du - t < lmin:
				kind = 2
			elif n >= CAP:
				kind = 3
			elif n > 0 and wk[i] + (abs(last[i] % BW - k % BW) + abs(last[i] // BW - k // BW)) * 200 + 215 > WB:
				kind = 3
			else:
				kind = 0
		if kind == 0:
			break
		if t < tlim:
			harvest()
			plant(SUN)
			v = measure()
			continue
		if kind == 1:
			# scarto senza tempo per rilanciare: resta, lo toglie la semina dopo
			return v
		if t < th - 0.3:
			# non crescerebbe in tempo o sfora la fase: meglio la cella vuota
			harvest()
			return 0
		break
	# acqua dosata: serve 1+4w >= WF/L, L = secondi che mancano alla fase di questo valore
	left = du - get_time()
	if left < WL:
		w = get_water()
		if left <= 0.05:
			x = 9
		else:
			x = WF / left - 1 - 4 * w
		add = x // 1
		if add < x:
			add += 1
		if add > 4:
			add = 4
		m = (1 - w) * 4
		mm = m // 1
		if mm < m:
			mm += 1
		if add > mm:
			add = mm
		if add > 0:
			if not use_item(WATER, add):
				if add > 1:
					use_item(WATER, 1)
	return v


def plant_sweep(lst, cur, first, tp, th, ex, lmin):
	# serpentina sulle 8 righe del blocco partendo dalla cella cur (0 o 31), con direzioni fisse;
	# ogni cella tenuta finisce nella lista del suo valore, nell'ordine della serpentina
	if cur == 0:
		order = ORDER0
		dirs = DIRS0
	else:
		order = ORDER31
		dirs = DIRS31
	wk = __ZEROS__
	last = __ZEROS__
	i = 0
	for k in order:
		if i > 0:
			move(dirs[i - 1])
		i += 1
		if first:
			if get_ground_type() != SOIL:
				till()
		if get_entity_type() != None:
			harvest()
		v = plant_cell(k, th, ex, lmin, tp - (32 - i) * TAU, lst, wk, last)
		if v >= MINV:
			j = v - MINV
			if len(lst[j]) > 0:
				wk[j] += (abs(last[j] % BW - k % BW) + abs(last[j] // BW - k // BW)) * 200 + 215
			else:
				wk[j] = 215
			last[j] = k
			lst[j].append(k)
	return order[31]


def harvest_phase(L, cur):
	# percorre la lista dall'estremo piu' vicino; -1 = obiettivo raggiunto
	n = len(L)
	if n == 0:
		return cur
	a = L[0]
	b = L[n - 1]
	cx = cur % BW
	cy = cur // BW
	if abs(a % BW - cx) + abs(a // BW - cy) <= abs(b % BW - cx) + abs(b // BW - cy):
		for k in L:
			cur = go_to_k(k, cur)
			harvest()
			if num_items(POWER) >= STOP:
				return -1
	else:
		i = n - 1
		while i >= 0:
			cur = go_to_k(L[i], cur)
			harvest()
			if num_items(POWER) >= STOP:
				return -1
			i -= 1
	return cur


def run(b, t0, main):
	goto(BW * (b % 8), BH * (b // 8))
	lst = []
	for _ in range(16 - MINV):
		lst.append([])
	cur = 0
	t = t0
	r = 0
	while True:
		if r == 0:
			pw = P_W0
			gw = G_W0
			ex = PH_W0 - PH_W
		else:
			pw = P_W
			ex = 0
			if r - 1 < len(GW):
				gw = GW[r - 1]
			else:
				gw = G_INF
		if r < len(LM):
			lmin = LM[r]
		else:
			lmin = L_INF
		tp = t + pw
		th = tp + gw
		# la serpentina parte da 0 o da 31: vai all'angolo piu' vicino
		if cur // BW < BH // 2:
			cur = go_to_k(0, cur)
		else:
			cur = go_to_k(31, cur)
		cur = plant_sweep(lst, cur, r == 0, tp, th, ex, lmin)
		if main:
			quick_print("round", r, "piantato a", get_time(), "finestra fino a", tp, "power", num_items(POWER))
		wait_until(th)
		v = 15
		while v >= MINV:
			if r == 0 and v == 15:
				th += PH_W0
			else:
				th += PH_W
			cur = harvest_phase(lst[v - MINV], cur)
			if cur < 0:
				clear()
				return
			lst[v - MINV] = []
			if main:
				quick_print("fase", v, "finita a", get_time(), "fino a", th, "power", num_items(POWER))
			wait_until(th)
			v -= 1
		t = th
		r += 1


def spawn_range(lo, hi, t0):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(spawn_range_task(mid, hi, t0))
		hi = mid
	run(lo, t0, False)


def spawn_range_task(lo, hi, t0):
	def fn():
		spawn_range(lo, hi, t0)
	return fn


T0 = get_time()
spawn_drone(spawn_range_task(1, 32, T0))
run(0, T0, True)
'''


def fmt(x):
    s = ('%.3f' % x).rstrip('0')
    return s + '0' if s.endswith('.') else s


def lists(x, eps=0.011):
    gl = [x['ginf'] + (x['g1'] - x['ginf']) * math.exp(-i / x['gtau']) for i in range(40)]
    ll = [x['linf'] + (x['l0'] - x['linf']) * math.exp(-i / x['ltau']) for i in range(40)]
    # tronca dove la lista e' ormai al valore limite
    ng = max(1, next((i for i, g in enumerate(gl) if abs(g - x['ginf']) < eps), 40))
    nl = max(1, next((i for i, l in enumerate(ll) if abs(l - x['linf']) < eps), 40))
    return [round(g, 2) for g in gl[:ng]], [round(l, 2) for l in ll[:nl]]


def params(x):
    """Parametri prog11 identici a quelli che finiscono nello script (liste troncate)."""
    gl, ll = lists(x)
    return dict(MERGE15=False, DEFER=False, PREPOS=False, PACE=True, GW_LIST=gl, G_W=round(x['ginf'], 2),
                LMIN_LIST=ll, LMIN=round(x['linf'], 2), P_W=x['pw'], PH_W=x['ph'], WB=x['wb'], CAP=int(x['cap']),
                TAU=x['tau'], WF=x['wf'], WL=x['wl'], P_W0=x['pw0'], G_W0=x['gw0'], PH_W0=x['ph0'],
                MINV=int(x['minv']))


def render(x, t10='?', t11='?'):
    gl, ll = lists(x)
    rep = {
        '__MINV__': str(int(x['minv'])), '__CAP__': str(int(x['cap'])), '__WB__': str(int(x['wb'])),
        '__P_W__': fmt(x['pw']), '__P_W0__': fmt(x['pw0']), '__G_W0__': fmt(x['gw0']), '__PH_W__': fmt(x['ph']),
        '__PH_W0__': fmt(x['ph0']), '__GW__': '[' + ', '.join(fmt(g) for g in gl) + ']',
        '__G_INF__': fmt(round(x['ginf'], 2)), '__LM__': '[' + ', '.join(fmt(l) for l in ll) + ']',
        '__L_INF__': fmt(round(x['linf'], 2)), '__TAU__': fmt(x['tau']), '__WF__': fmt(x['wf']), '__WL__': fmt(x['wl']),
        '__ZEROS__': '[' + ', '.join(['0'] * (16 - int(x['minv']))) + ']', '__T10__': t10, '__T11__': t11,
    }
    s = TEMPLATE
    for k, v in rep.items():
        s = s.replace(k, v)
    assert '__' not in s.replace('__name__', ''), [w for w in s.split() if '__' in w][:5]
    return s


if __name__ == '__main__':
    x = json.load(open(sys.argv[1]))
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'v11_draft.py')
    t10 = sys.argv[3] if len(sys.argv) > 3 else '?'
    t11 = sys.argv[4] if len(sys.argv) > 4 else '?'
    open(out, 'w').write(render(x, t10, t11))
    print('scritto', out)
