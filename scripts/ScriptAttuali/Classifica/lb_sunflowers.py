# Classifica Sunflowers: 100.000 power, 32 droni. v5 del 6 nov 2026.
# v4 (colonne, 3:04.9) e' stata battuta da un 2:09.7. Qui ogni drone lavora su un blocco 4x8
# invece che su una colonna: in ogni fase visita SOLO le celle del valore da raccogliere con un
# giro greedy (nel blocco la distanza massima e' 10, non 31): ~14-18 mosse per fase invece di 31,
# fase da ~1.0 s invece di 1.35. Il resto (round sincronizzati con get_time, reroll solo nella
# finestra di piantagione, acqua dosata sul tempo che manca alla fase, CAP per valore) e' la v4.
#
# Regole: petali = Next(7,16) a ogni plant; bonus x8 se petali == massimo del campo (semi inclusi)
# e >= 10 girasoli; ogni harvest (anche di un seme) aggiorna il flag che toglie il bonus al
# raccolto successivo se l'ultimo non era un massimo; power iniziale 0 (meta' velocita').
GOAL = 100000
MINV = 11
P_W = 4.4      # s: finestra di piantagione (misurato: il main chiude fra 3.5 e 4.4 s)
P_W0 = 11.5    # s: primo round a meta' velocita'
G_W = 1.2      # s: attesa crescita dopo la finestra
G_W0 = 5.3     # s: primo round, crescita quasi secca
PH_W = 1.15    # s: fase di raccolta (con 1.0 il main sforava di 0.1-0.2 s e il round perdeva ~800 power)
PH_W0 = 1.5    # s: prima fase del primo round (parte a velocita' dimezzata)
CAP = 9        # celle per valore per blocco

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


def bad(v, th, cnt):
	if v < MINV:
		return True
	if cnt[v - MINV] >= CAP:
		return True
	if v == 15 and th - get_time() < 2.0:
		return True
	return False


def plant_cell(deadline, th, cnt):
	plant(SUN)
	v = measure()
	while get_time() < deadline and bad(v, th, cnt):
		harvest()
		plant(SUN)
		v = measure()
	while v >= 14 and get_time() >= deadline:
		harvest()
		plant(SUN)
		v = measure()
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
	if v >= MINV:
		cnt[v - MINV] += 1
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


def plant_sweep(vals, cur, first, deadline, th):
	# serpentina sulle 8 righe del blocco partendo dalla cella cur (0 o 31)
	cnt = [0, 0, 0, 0, 0]
	if cur == 0:
		order = [0, 1, 2, 3, 7, 6, 5, 4, 8, 9, 10, 11, 15, 14, 13, 12, 16, 17, 18, 19, 23, 22, 21, 20, 24, 25, 26, 27, 31, 30, 29, 28]
	else:
		order = [31, 30, 29, 28, 24, 25, 26, 27, 23, 22, 21, 20, 16, 17, 18, 19, 15, 14, 13, 12, 8, 9, 10, 11, 7, 6, 5, 4, 0, 1, 2, 3]
	for k in order:
		cur = go_to_k(k, cur)
		if first:
			if get_ground_type() != SOIL:
				till()
		t = get_entity_type()
		if t == SUN and vals[k] >= MINV:
			cnt[vals[k] - MINV] += 1
		else:
			if t != None:
				harvest()
			vals[k] = plant_cell(deadline, th, cnt)
	return cur


def harvest_phase(vals, cur, v, main):
	# giro greedy sulle celle con valore v
	todo = []
	for k in range(32):
		if vals[k] == v:
			todo.append(k)
	cx = cur % BW
	cy = cur // BW
	while len(todo) > 0:
		best = 0
		bd = 99
		j = 0
		while j < len(todo):
			k = todo[j]
			d = abs(k % BW - cx) + abs(k // BW - cy)
			if d < bd:
				bd = d
				best = j
			j += 1
		k = todo.pop(best)
		cur = go_to_k(k, cur)
		cx = k % BW
		cy = k // BW
		harvest()
		vals[k] = 0
		if main and num_items(POWER) >= GOAL:
			return -1
	return cur


def run(b, t0, main):
	goto(BW * (b % 8), BH * (b // 8))
	vals = []
	for _ in range(32):
		vals.append(0)
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
		cur = plant_sweep(vals, cur, r == 0, t + pw, th)
		if main:
			quick_print("round", r, "piantato a", get_time(), "finestra fino a", t + pw, "power", num_items(POWER))
		wait_until(th)
		v = 15
		while v >= MINV:
			cur = harvest_phase(vals, cur, v, main)
			if cur < 0:
				clear()
				return
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


clear()
T0 = get_time()
spawn_drone(spawn_range_task(1, 32, T0))
run(0, T0, True)
