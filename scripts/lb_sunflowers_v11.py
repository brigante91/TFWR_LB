# Classifica Sunflowers: 100.000 power, 32 droni. v11 del 10 nov 2026 (dalla v10, 2:37.964).
# Stesso impianto (blocco 4x8 per drone, semina a serpentina, fasi sincronizzate con get_time dal
# valore 15 a MINV), con quattro modifiche misurate nel simulatore tarato (haysim/sun2/prog11.py,
# stesse regole di haysim/sunsim2.py):
# 1. Semina a ritmo: un rilancio si fa solo se il resto della serpentina sta ancora nella
#    finestra (tp - celle_rimaste * TAU); chi e' in ritardo non rilancia piu'.
# 2. Tetto di lavoro per fase: oltre a CAP celle per valore, il giro di ogni valore (mosse fra
#    le celle in ordine di semina * 200 + 215 a cella) non deve superare WB tick: la fase piu'
#    lunga si accorcia e la finestra PH_W scende da 0.85 a 0.72 s.
# 3. Rilancio dei semi che non farebbero in tempo a crescere: se alla fase del valore mancano
#    meno di LM[round] secondi (tanti nei primi round asciutti, pochi dopo) il seme si rilancia.
# 4. Attesa di crescita che cala coi round (GW): lunga finche' il campo e' asciutto, poi corta.
# Simulatore (16 semi, obiettivo 90-110k riscalato): v10 2:39.7, v11 2:29.2 (-10.5 +- 0.7 s).
# Lo script vero eseguito sul mondo simulato (haysim/sun2/harness.py, 4 semi): v10 2:38.2,
# v11 2:25.0. Il guadagno resta (-10..-12 s) con crescita 6.6/7.4 s, serbatoio -10%, codice +60%.
# Quanto pesa ogni modifica (toglierla costa): tetto di lavoro 5.5 s, GW 3.4 s, LM 0.7 s, ritmo 0.3 s.
# Provate e scartate (nessun guadagno): spostarsi nel tempo morto sul capo della lista dopo,
# 15 raccolti nell'attesa di crescita, ripianto a cascata (anche con azioni allineate a un
# battito di tick), 8 o 9 livelli, attesa della crescita sulla cella, sincronia a tick.
#
# Regole: petali = Next(7,16) a ogni plant; bonus x8 se petali == massimo del campo (semi inclusi)
# e >= 10 girasoli; ogni harvest (anche di un seme) aggiorna il flag che toglie il bonus al
# raccolto successivo se l'ultimo non era un massimo; power iniziale 0 (meta' velocita').
GOAL = 100000
STOP = GOAL + 10   # margine contro il UsePower fra il controllo e la fine della run
MINV = 9
CAP = 8        # celle per valore per blocco
WB = 3800      # tick: lavoro massimo del giro di un valore
P_W = 3.8      # s: finestra di semina
P_W0 = 10.5    # s: primo round a meta' velocita'
G_W0 = 4.5     # s: primo round, crescita quasi secca
PH_W = 0.72    # s: fase di raccolta
PH_W0 = 1.5    # s: prima fase del primo round (parte a velocita' dimezzata)
GW = [1.75, 1.45, 1.22, 1.04, 0.9, 0.79, 0.7, 0.63, 0.58, 0.54, 0.51, 0.49, 0.47, 0.45, 0.44, 0.43, 0.42, 0.42, 0.41, 0.41]   # s: attesa di crescita del round 1, 2, ...
G_INF = 0.4
LM = [3.0, 2.65, 2.37, 2.16, 1.99, 1.86, 1.76, 1.68, 1.62, 1.57, 1.53, 1.5, 1.48, 1.46, 1.45, 1.44, 1.43, 1.42, 1.42, 1.41]   # s: tempo minimo fra semina e fase, round 0, 1, ...
L_INF = 1.4
TAU = 0.083    # s per cella rimasta: sotto questo margine niente rilanci
WF = 7.0       # acqua: 1+4w >= WF/L
WL = 7.0       # acqua solo se mancano meno di WL secondi alla fase

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
	wk = [0, 0, 0, 0, 0, 0, 0]
	last = [0, 0, 0, 0, 0, 0, 0]
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
