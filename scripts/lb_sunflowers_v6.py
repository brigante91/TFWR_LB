# Classifica Sunflowers: 100.000 power, 32 droni, campo 32x32. v6 del 6 nov 2026.
# STRATEGIA A PIPELINE (progettata e misurata con haysim/sunsim.py).
#
# Differenza con v4/v5 (a finestra): niente finestra di piantagione piena a ogni round.
# Durante la fase v (si raccolgono i girasoli col valore massimo v) ogni drone, subito dopo
# aver raccolto una cella, la RIPIANTA. Il nuovo valore u letto da measure():
#   - u <= v-CASCADE_GAP : tenuto. Se u >= MINV e' un seme "a cascata": cresce entro la sua
#       fase u e viene RI-raccolto nello stesso round (una cella puo' rendere piu' volte).
#       Se u < MINV e' una cella morta ma INNOCUA: il suo valore e' sotto tutte le fasi,
#       quindi non e' mai il massimo e non toglie il bonus a nessuno; verra' riempita nella
#       mini-finestra di fine round.
#   - u >= v-CASCADE_GAP+1 : inquinerebbe le fasi ancora da fare (resterebbe un valore > del
#       massimo di quelle fasi) -> reroll con harvest+plant. Il reroll raccoglie un seme
#       non-massimo: sporca il flag globale e toglie il bonus al raccolto successivo di
#       CHIUNQUE (costa ~7 power oltre a 403 tick), per questo si rerolla il meno possibile.
#
# SICUREZZA sul bonus: in ogni fase si raccolgono TUTTE le celle con quel valore, cresciute
# o no. Un seme a cascata non cresciuto in tempo viene comunque raccolto nella SUA fase u
# (resa 0 ma rimosso), dove u e' ancora il massimo: il flag resta pulito e il seme non
# sopravvive per inquinare le fasi piu' basse. Cosi' la pipeline non puo' rompere il bonus.
#
# Le fasi sono sincronizzate con get_time() e costanti uguali per tutti (niente comunicazione
# fra droni): un drone in ritardo che lasciasse in campo un valore massimo toglierebbe il
# bonus a tutti, quindi ogni finestra deve coprire il drone piu' lento su 32.
#
# NOTA dal simulatore (haysim/sunsim.py, media su 40 seed): la pipeline pareggia la strategia
# a finestra (~2:40 simulati) ma NON la batte, perche' la crescita (~1 s) e' piu' lunga di una
# fase (~0.4 s): i semi a cascata spesso non fanno in tempo a crescere e i reroll ai bordi
# costano bonus. La via piu' rapida nel simulatore resta la v5 a finestra con margini stretti.
# Questa v6 e' la variante a pipeline richiesta, tarata sulla sua configurazione migliore
# (CASCADE_GAP=2, LOW_STOP=13: cascata solo nelle fasi 15 e 14). Col simulatore LOW_STOP=12
# (cascata anche a fase 13) peggiora a ~3:11 perche' li' i reroll per non inquinare costano
# troppo bonus. Usare la v6 solo se un test reale conferma il guadagno sulla v5.
GOAL = 100000
MINV = 11
CASCADE_GAP = 2      # tieni il replant solo se u <= v-CASCADE_GAP (cresce e non inquina)
LOW_STOP = 13        # a questa fase o sotto non si ripianta (mini-finestra): cascata 15,14
P_W0 = 11.5          # s: prima finestra piena a meta' velocita' (seed del campo)
G_W0 = 5.3           # s: prima crescita (quasi secca)
G_W = 1.0            # s: buffer di crescita dopo la mini-finestra
MW_W = 3.2           # s: mini-finestra (riempi le celle vuote per il round dopo)
PH_W = 1.15          # s: fase di raccolta+ripianto (deve coprire il drone piu' lento)
PH_W0 = 1.5          # s: prima fase del primo round (parte a velocita' dimezzata)
CAP = 9              # celle per valore per blocco

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


def go_to_k(k, cur):
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


def water_for(left):
	# dosa l'acqua perche' 1+4w >= 5/left (crescita 5 s / (1+4w)); serbatoio permettendo
	if left >= 5.0:
		return
	x = (5.0 / left - 1.0) / 4.0 - get_water()
	add = x // 0.25
	if add * 0.25 < x:
		add += 1
	if add > 4:
		add = 4
	if add > 0:
		if not use_item(WATER, add):
			if add > 1:
				use_item(WATER, 1)


def plant_min(deadline):
	# pianta finche' valore >= MINV (usato nella finestra piena e nella mini-finestra:
	# fasi flag-safe, nessuno raccoglie, i reroll non costano bonus)
	plant(SUN)
	v = measure()
	while v < MINV and get_time() < deadline:
		harvest()
		plant(SUN)
		v = measure()
	return v


def full_window(vals, cur, th):
	# primo round: pianta tutte e 32 le celle del blocco (serpentina), reroll >= MINV
	cnt = [0, 0, 0, 0, 0]
	if cur == 0:
		order = [0, 1, 2, 3, 7, 6, 5, 4, 8, 9, 10, 11, 15, 14, 13, 12, 16, 17, 18, 19, 23, 22, 21, 20, 24, 25, 26, 27, 31, 30, 29, 28]
	else:
		order = [31, 30, 29, 28, 24, 25, 26, 27, 23, 22, 21, 20, 16, 17, 18, 19, 15, 14, 13, 12, 8, 9, 10, 11, 7, 6, 5, 4, 0, 1, 2, 3]
	deadline = th - 0.4
	for k in order:
		cur = go_to_k(k, cur)
		if get_ground_type() != SOIL:
			till()
		t = get_entity_type()
		if t != None:
			harvest()
		plant(SUN)
		v = measure()
		while get_time() < deadline and (v < MINV or cnt[v - MINV] >= CAP):
			harvest()
			plant(SUN)
			v = measure()
		if v >= MINV:
			cnt[v - MINV] += 1
		else:
			v = 0
		# acqua per crescere entro la sua fase (15-v fasi dopo la crescita)
		if v >= MINV:
			water_for(th + (15 - v) * PH_W - get_time())
		vals[k] = v
	return cur


def mini_window(vals, cur, th):
	# riempi solo le celle vuote (vals==0); fase sincronizzata, flag-safe
	todo = []
	for k in range(32):
		if vals[k] == 0:
			todo.append(k)
	cx = cur % BW
	cy = cur // BW
	deadline = th - 0.3
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
		v = plant_min(deadline)
		if v < MINV:
			v = 0
		else:
			water_for(th + (15 - v) * PH_W + MW_W - get_time())
		vals[k] = v
	return cur


def harvest_phase(vals, cur, v, th, main):
	# giro greedy sulle celle con valore v: raccogli e (se v alta) ripianta a cascata
	replant = v > LOW_STOP and v - CASCADE_GAP >= MINV
	hi = v - CASCADE_GAP
	todo = []
	for k in range(32):
		if vals[k] == v:
			todo.append(k)
	cx = cur % BW
	cy = cur // BW
	deadline = th - 0.25
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
		if main and num_items(POWER) >= GOAL:
			return -1
		if replant and get_time() < deadline:
			plant(SUN)
			u = measure()
			while u > hi and get_time() < deadline:
				harvest()
				plant(SUN)
				u = measure()
			if u <= hi and u >= MINV:
				water_for(th + (v - u) * PH_W - get_time())
				vals[k] = u
			else:
				# u < MINV (morta, innocua) oppure niente tempo: lascia vuota
				if u > hi:
					harvest()
				vals[k] = 0
		else:
			vals[k] = 0
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
		# --- piantagione: finestra piena al round 0, mini-finestra dopo ---
		if r == 0:
			th = t + P_W0 + G_W0
			if cur // BW < BH // 2:
				cur = go_to_k(0, cur)
			else:
				cur = go_to_k(31, cur)
			cur = full_window(vals, cur, t + P_W0)
			wait_until(th)
		else:
			th = t + MW_W + G_W
			cur = mini_window(vals, cur, t + MW_W)
			wait_until(th)
		if main:
			quick_print("round", r, "piantato a", get_time(), "fino a", th, "power", num_items(POWER))
		# --- fasi di raccolta 15..MINV con ripianto a cascata ---
		v = 15
		while v >= MINV:
			cur = harvest_phase(vals, cur, v, th, main)
			if cur < 0:
				clear()
				return
			if main:
				quick_print("fase", v, "finita a", get_time(), "scad", th + PH_W, "power", num_items(POWER))
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
