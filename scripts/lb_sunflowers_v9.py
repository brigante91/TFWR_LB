# Classifica Sunflowers: 100.000 power, 32 droni. v9 del 7 nov 2026 (dalla bozza della v7).
# Taratura sui test in gioco del 7 nov: il simulatore (haysim/sunsim2.py + sunprog.py) riproduce
# le tre versioni provate SOLO con una crescita media del girasole di 7 s (non 5) e il serbatoio
# normale (25.6 unita'/s):
#                       in gioco      simulatore tarato (obiettivo fisso, 120 seed)
#   bozza v7            2:42.9        2:44.431 +- 0.070
#   v7 finale           2:50.2        2:50.682 +- 0.125
#   v8                  3:16.0 (1)    3:16.504 +- 0.140
# Con la crescita a 7 s l'acqua serve di piu': v7 e v8 ne davano meno e sono peggiorate.
# Modifiche rispetto alla bozza (MINV 9, liste per valore, stop da qualunque drone a GOAL+10):
# 1. Piu' acqua mirata: 1+4w >= 7/L (bozza 6.25) e anche se L < 7 s (bozza 6).
# 2. P_W 3.6 -> 3.8: con l'acqua in piu' la semina ha bisogno di un po' piu' di tempo.
# 3. Round 0 un po' piu' corto: P_W0 10.5, G_W0 4.5 (bozza 11.5 / 5.3); PH_W0 resta 1.5.
# Misura nel simulatore tarato (120 seed, errore standard; differenza appaiata con la bozza):
#                       obiettivo fisso                obiettivo 90-110k riscalato
#   v5 P_W 4.4          2:57.529 +- 0.084              2:56.119 +- 0.197
#   bozza v7            2:44.431 +- 0.070              2:43.440 +- 0.198
#   v9                  2:38.560 +- 0.092 (-5.9)       2:39.975 +- 0.194 (-3.5)
# Il guadagno vero da aspettarsi e' quello della seconda colonna: la prima dipende anche da dove
# cade il superamento di 100.000 nell'ultimo round.
# Misurate e scartate col simulatore tarato: acqua nelle fasi sulle celle appena raccolte e
# riempire le celle fino a 1 (svuotano il serbatoio: +20..+40 s), raccolta anticipata dei 15 nel
# round 0, mini-round finale, G_W piu' lungo, MINV 8, CAP 7.
#
# Regole: petali = Next(7,16) a ogni plant; bonus x8 se petali == massimo del campo (semi inclusi)
# e >= 10 girasoli; ogni harvest (anche di un seme) aggiorna il flag che toglie il bonus al
# raccolto successivo se l'ultimo non era un massimo; power iniziale 0 (meta' velocita').
GOAL = 100000
STOP = GOAL + 10   # margine contro il UsePower fra il controllo e la fine della run
MINV = 9
P_W = 3.8      # s: finestra di piantagione
P_W0 = 10.5    # s: primo round a meta' velocita'
G_W = 0.85     # s: attesa crescita dopo la finestra
G_W0 = 4.5     # s: primo round, crescita quasi secca
PH_W = 0.85    # s: fase di raccolta
PH_W0 = 1.5    # s: prima fase del primo round (parte a velocita' dimezzata)
CAP = 6        # celle per valore per blocco
NO15 = 1.5     # s: niente 15 se mancano meno di NO15 secondi alla prima fase
WF = 7.0       # acqua: 1+4w >= WF/L (bozza: 6.25)
WL = 7.0       # acqua solo se mancano meno di WL secondi alla fase (bozza: 6.0)

S = get_world_size()
SUN = Entities.Sunflower
SOIL = Grounds.Soil
WATER = Items.Water
POWER = Items.Power
BW = 4
BH = 8


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


def bad(v, th, lst):
	if v < MINV:
		return True
	if len(lst[v - MINV]) >= CAP:
		return True
	if v == 15 and th - get_time() < NO15:
		return True
	return False


def plant_cell(deadline, th, lst):
	plant(SUN)
	v = measure()
	while get_time() < deadline and bad(v, th, lst):
		harvest()
		plant(SUN)
		v = measure()
	while v >= 14 and get_time() >= deadline:
		harvest()
		plant(SUN)
		v = measure()
	if v >= MINV:
		# acqua dosata: serve 1+4w >= WF/L, L = secondi che mancano alla fase di questo valore
		left = th + (15 - v) * PH_W - get_time()
		if left < WL:
			x = WF / left - 1 - 4 * get_water()
			add = x // 1
			if add < x:
				add += 1
			if add > 4:
				add = 4
			if add > 0:
				if not use_item(WATER, add):
					if add > 1:
						use_item(WATER, 1)
	return v


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


def plant_sweep(lst, cur, first, deadline, th):
	# serpentina sulle 8 righe del blocco partendo dalla cella cur (0 o 31); ogni cella
	# tenuta (v >= MINV) finisce nella lista del suo valore, nell'ordine della serpentina
	if cur == 0:
		order = [0, 1, 2, 3, 7, 6, 5, 4, 8, 9, 10, 11, 15, 14, 13, 12, 16, 17, 18, 19, 23, 22, 21, 20, 24, 25, 26, 27, 31, 30, 29, 28]
	else:
		order = [31, 30, 29, 28, 24, 25, 26, 27, 23, 22, 21, 20, 16, 17, 18, 19, 15, 14, 13, 12, 8, 9, 10, 11, 7, 6, 5, 4, 0, 1, 2, 3]
	for k in order:
		cur = go_to_k(k, cur)
		if first:
			if get_ground_type() != SOIL:
				till()
		if get_entity_type() != None:
			harvest()
		v = plant_cell(deadline, th, lst)
		if v >= MINV:
			lst[v - MINV].append(k)
	return cur


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
		else:
			pw = P_W
			gw = G_W
		th = t + pw + gw
		# la serpentina parte da 0 o da 31: vai all'angolo piu' vicino
		if cur // BW < BH // 2:
			cur = go_to_k(0, cur)
		else:
			cur = go_to_k(31, cur)
		cur = plant_sweep(lst, cur, r == 0, t + pw, th)
		if main:
			quick_print("round", r, "piantato a", get_time(), "finestra fino a", t + pw, "power", num_items(POWER))
		wait_until(th)
		v = 15
		while v >= MINV:
			cur = harvest_phase(lst[v - MINV], cur)
			if cur < 0:
				clear()
				return
			lst[v - MINV] = []
			if main:
				quick_print("fase", v, "finita a", get_time(), "fino a", th + PH_W, "power", num_items(POWER))
			if r == 0 and v == 15:
				th += PH_W0
			else:
				th += PH_W
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
