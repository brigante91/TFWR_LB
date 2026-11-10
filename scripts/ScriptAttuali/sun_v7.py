# Classifica Sunflowers: 100.000 power, 32 droni. v7 del 7 nov 2026 (dalla v5 a blocchi 4x8).
# Misurata col simulatore a eventi haysim/sunsim2.py + haysim/sunprog.py (trascrizione dello
# script coi costi dell'interprete, regole da decompiled_full/Core). Media su 300 seed:
#   v5 P_W 5.0 : 2:53.1   v5 P_W 4.4 : 2:48.1   v7 : vedi riga "MISURA" sotto
# Modifiche rispetto alla v5:
# 1. MINV 11 -> 9 (sette fasi 15..9): si accettano 7 valori su 9, i reroll per cella scendono
#    da 0.8 a 0.29 (ogni reroll costa 401 tick), la finestra si accorcia (P_W 3.6) e ogni fase
#    ha meno celle per blocco (CAP 6), quindi fasi da 0.85 s. E' la modifica che rende di piu'.
# 2. Liste per valore costruite durante la finestra, nell'ordine della serpentina: la fase
#    percorre la sua lista dall'estremo piu' vicino. Niente scansione dei 32 valori ne' giro
#    greedy O(n^2) a ogni fase (~130 + 13*n*n/2 operazioni): -1.0 s da sola.
# 3. Fine run: QUALUNQUE drone controlla il power dopo ogni raccolto e chiama clear() (clear()
#    toglie tutti gli altri droni e la run finisce quando chi l'ha chiamato ritorna). Soglia
#    GOAL + 10: Farm.UsePower toglie ogni 0.2 s il consumo accumulato (fino a ~6.5 power con 32
#    droni); se scatta nei 200 tick di clear() con la soglia esatta la run puo' finire sotto
#    100.000, e una run fallita fa fallire l'invio.
# 4. G_W 1.2 -> 0.85 e i 15 rifiutati solo se mancano meno di 1.5 s (non 2.0) a th.
# 5. Niente clear() iniziale (200 tick a meta' velocita'): in classifica il campo e' nuovo e
#    lo script non dipende dallo stato iniziale (till se serve, harvest se c'e' un'entita').
#
# Regole: petali = Next(7,16) a ogni plant; bonus x8 se petali == massimo del campo (semi inclusi)
# e >= 10 girasoli; ogni harvest (anche di un seme) aggiorna il flag che toglie il bonus al
# raccolto successivo se l'ultimo non era un massimo; power iniziale 0 (meta' velocita').
GOAL = 100000
STOP = GOAL + 10   # margine contro il UsePower fra il controllo e la fine della run
MINV = 9
P_W = 3.6      # s: finestra di piantagione
P_W0 = 11.5    # s: primo round a meta' velocita'
G_W = 0.85     # s: attesa crescita dopo la finestra
G_W0 = 5.3     # s: primo round, crescita quasi secca
PH_W = 0.85    # s: fase di raccolta
PH_W0 = 1.5    # s: prima fase del primo round (parte a velocita' dimezzata)
CAP = 6        # celle per valore per blocco
NO15 = 1.5     # s: niente 15 se mancano meno di NO15 secondi alla prima fase

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
		# acqua dosata: serve 1+4w >= 6.25/L, L = secondi che mancano alla fase di questo valore
		left = th + (15 - v) * PH_W - get_time()
		if left < 6.0:
			x = 6.25 / left - 1 - 4 * get_water()
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
