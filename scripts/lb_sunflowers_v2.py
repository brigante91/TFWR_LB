# Classifica Sunflowers: 100.000 power, 32 droni. v3 del 6 nov 2026 (v2 = 3:20.094, #2).
#
# Regole lette da Sunflower.cs / Farm.cs:
#  - petali = Next(7, 16) a ogni plant, NON in cache: il reroll funziona subito sul seme.
#  - bonus x8 se petali == massimo fra TUTTI i girasoli in campo (semi compresi) e ce ne sono >= 10.
#  - OGNI harvest, anche di un seme, aggiorna il flag "ultimo raccolto sbagliato": se l'ultimo
#    harvest nel mondo non era un massimo, il raccolto successivo (di chiunque) perde il bonus.
#    I reroll avvengono solo nella finestra di piantagione, quando nessuno raccoglie.
#  - power iniziale 0: simulazione a meta' velocita' fino al primo raccolto; consumo ~1 power/s
#    per drone (32/s), anche in attesa.
#  - crescita 5 s / (1 + 4*acqua) +-20%; serbatoio 25.6 acqua/s: non basta per tutti, quindi
#    l'acqua e' dosata sul tempo che manca alla fase di quel valore (la prima unita' vale 2.5 s).
# Strategia: round sincronizzati con get_time() (0 tick), stesso programma per tutti:
#  1) finestra di piantagione: reroll finche' petali >= MINV; un 15 estratto troppo tardi per
#     crescere viene rerollato; dopo la scadenza si accettano solo valori <= 13;
#  2) attesa crescita; 3) fasi di raccolta 15, 14, ...: in ogni fase si raccolgono solo i
#     girasoli con quel valore (il massimo del campo). Ogni colonna tiene al massimo CAP celle
#     per valore (reroll in piu'), cosi' la fase piu' lunga fra 32 colonne resta corta.
#     (v3 provava a saltare la fase 11 nei round pari: 3:27, peggio, perche' la finestra di
#     piantagione non si accorcia con meno celle.)
GOAL = 100000
MINV = 11
P_W = 4.6      # s: finestra di piantagione (misurato 3.5-4.2 s senza CAP; CAP aggiunge ~0.3)
P_W0 = 11.2    # s: primo round a meta' velocita' (spawn, till, plant con reroll)
G_W = 1.2      # s: attesa crescita dopo la finestra
G_W0 = 5.3     # s: primo round, crescita quasi secca
PH_W = 1.35    # s: fase di raccolta (31 mosse + al massimo CAP harvest)
PH_W0 = 1.8    # s: prima fase del primo round, parte a velocita' dimezzata (misurato 1.2 s)
CAP = 9        # celle per valore per colonna (senza limite il massimo su 32 colonne e' ~13)

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
		# in ritardo: un 15 o 14 non farebbe in tempo a crescere e resterebbe il massimo
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


def plant_sweep(vals, y, dy, first, deadline, th):
	if dy == 1:
		d = North
	else:
		d = South
	cnt = [0, 0, 0, 0, 0]
	for i in range(S):
		if first:
			if get_ground_type() != SOIL:
				till()
		t = get_entity_type()
		if t == SUN and vals[y] >= MINV:
			cnt[vals[y] - MINV] += 1
		else:
			if t != None:
				harvest()
			vals[y] = plant_cell(deadline, th, cnt)
		if i < S - 1:
			move(d)
			y += dy


def harvest_sweep(vals, y, dy, v, main):
	if dy == 1:
		d = North
	else:
		d = South
	for i in range(S):
		if vals[y] == v:
			harvest()
			vals[y] = 0
			if main and num_items(POWER) >= GOAL:
				return True
		if i < S - 1:
			move(d)
			y += dy
	return False


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
		else:
			pw = P_W
			gw = G_W
		th = t + pw + gw
		plant_sweep(vals, y, dy, r == 0, t + pw, th)
		y += dy * (S - 1)
		dy = -dy
		if main:
			quick_print("round", r, "piantato a", get_time(), "finestra fino a", t + pw, "power", num_items(POWER))
		wait_until(th)
		v = 15
		while v >= MINV:
			done = harvest_sweep(vals, y, dy, v, main)
			if done:
				clear()
				return
			y += dy * (S - 1)
			dy = -dy
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
spawn_drone(spawn_range_task(1, S, T0))
run(0, T0, True)
