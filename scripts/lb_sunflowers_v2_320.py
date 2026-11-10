# Classifica Sunflowers: 100.000 power, 32 droni. v2 del 6 nov 2026 (mai inviata finora).
# Classifica Steam: #1 3:13, #4 3:43, solo 12 iscritti. Stima di questo script: ~3:00-3:10.
#
# Regole lette da Sunflower.cs / Farm.cs:
#  - petali = Next(7, 16) a ogni plant, NON in cache: il reroll funziona subito sul seme.
#  - bonus x8 se petali == massimo fra TUTTI i girasoli in campo (semi compresi) e ce ne sono >= 10.
#  - OGNI harvest, anche di un seme, aggiorna il flag "ultimo raccolto sbagliato": se l'ultimo
#    harvest nel mondo non era un massimo, il raccolto successivo (di chiunque) perde il bonus.
#    Il vecchio lb_sunflowers rerollava con harvest() mentre gli altri raccoglievano: quasi
#    nessun bonus. Qui i reroll avvengono solo nella finestra di piantagione, quando nessuno
#    raccoglie: costano UN solo bonus per round.
#  - il power parte da 0 e con power > 0 la simulazione va al doppio (3037 -> 6075 tick/s);
#    il consumo e' ~1 power/s per drone, trascurabile. Il primo round e' lento: finestre x2.
#  - livello sunflowers = 1: resa 1 power, 8 con bonus.
# Strategia: round sincronizzati con get_time() (costa 0 tick), stesso programma per tutti:
#  1) finestra di piantagione: ogni drone pianta la sua colonna, reroll finche' petali >= MINV
#     (primo round senza reroll: si pianta e basta, cosi' si arriva prima al primo power);
#  2) attesa crescita (5 s secca, 1 s con acqua 1.0): l'acqua si da' subito dopo il plant;
#  3) fasi di raccolta a valore decrescente 15, 14, ..., MINV: in ogni fase si raccolgono solo
#     i girasoli con quel valore, che e' il massimo del campo -> tutti con bonus x8.
GOAL = 100000
MINV = 11
P_W = 4.5      # s: finestra di piantagione (misurato: il main finisce fra 3.5 e 4.2 s)
P_W0 = 7.8     # s: primo round: spawn + till + plant senza reroll, a velocita' dimezzata (in gioco 6.9 s)
G_W = 1.5      # s: attesa crescita dopo la finestra
G_W0 = 5.3     # s: primo round, crescita secca
PH_W = 1.5     # s: fase di raccolta: 31 mosse + fino a ~14 harvest (max su 32 colonne)
PH_W0 = 2.7    # s: prima fase del primo round, parte a velocita' dimezzata

S = get_world_size()
SUN = Entities.Sunflower
SOIL = Grounds.Soil
WATER = Items.Water
POWER = Items.Power


def goto_x(x):
	if x <= S // 2:
		for _ in range(x):
			move(East)
	else:
		for _ in range(S - x):
			move(West)


def wait_until(t):
	while get_time() < t:
		pass


def plant_cell(minv, deadline, th):
	plant(SUN)
	v = measure()
	while v < minv and get_time() < deadline:
		harvest()
		plant(SUN)
		v = measure()
	# Acqua dosata: il girasole deve essere cresciuto all'inizio della SUA fase. Crescita
	# 5/(1+4w) s (+-20%): servono 1+4w >= 6.25/L con L = secondi che mancano alla fase.
	# La prima unita' vale piu' delle altre (5 s -> 2.5 s), quindi si da' solo il necessario:
	# il serbatoio (25.6/s) non basta per tutti e un 15 ancora seme alla fase 15 vale 0.
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


def plant_sweep(vals, y, dy, first, minv, deadline, th):
	if dy == 1:
		d = North
	else:
		d = South
	for i in range(S):
		if first:
			if get_ground_type() != SOIL:
				till()
		t = get_entity_type()
		if t == SUN and vals[y] >= MINV:
			pass
		else:
			if t != None:
				harvest()
			vals[y] = plant_cell(minv, deadline, th)
		if i < S - 1:
			move(d)
			y += dy


def harvest_sweep(vals, y, dy, v):
	if dy == 1:
		d = North
	else:
		d = South
	for i in range(S):
		if vals[y] == v:
			# anche se non e' cresciuto: un seme col valore massimo lasciato in campo
			# toglierebbe il bonus a tutte le fasi successive del round (perdo 8 power, non 7000)
			harvest()
			vals[y] = 0
		if i < S - 1:
			move(d)
			y += dy


def run(x, t0, main):
	goto_x(x)
	vals = []
	for _ in range(S):
		vals.append(0)
	y = 0
	dy = 1
	t = t0
	r = 0
	while True:
		if r == 0:
			pw = P_W0
			gw = G_W0
			minv = 7
		else:
			pw = P_W
			gw = G_W
			minv = MINV
		th = t + pw + gw
		plant_sweep(vals, y, dy, r == 0, minv, t + pw, th)
		y += dy * (S - 1)
		dy = -dy
		if main:
			quick_print("round", r, "piantato a", get_time(), "finestra fino a", t + pw, "power", num_items(POWER))
		wait_until(th)
		v = 15
		while v >= minv:
			harvest_sweep(vals, y, dy, v)
			y += dy * (S - 1)
			dy = -dy
			if main:
				quick_print("fase", v, "finita a", get_time(), "fino a", th + PH_W, "power", num_items(POWER))
			if main and num_items(POWER) >= GOAL:
				clear()
				return
			if r == 0 and v == 15:
				th += PH_W0
			else:
				th += PH_W
			wait_until(th)
			v -= 1
		t = th
		r += 1


def make_task(x, t0):
	def fn():
		run(x, t0, False)
	return fn


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
spawn_drone(spawn_range_task(1, S, T0))
run(0, T0, True)
