# Classifica Rice (2e6 riso, 32 droni, 32x32). v2 dell'8 nov 2026: versione snella di lb_rice.py v5.
# lb_rice.py v5 in gioco: 1:57.01. #1 1:51.900, #2 1:55.365.
#
# Stesso schema (vedi lb_rice.py): ogni drone ha una colonna di 32 celle e la percorre verso Nord
# (wrap). Per strato tre passate:
#   A2: scendi all'argilla e pianta;  B: raccogli, scava la terrazza secca, pianta sul 2o blocco;
#   A1: raccogli il 2o blocco (la terrazza secca la toglie il crollo nella A2 dopo).
# Celle con durezza > H_SKIP saltate (le abbassa il trascinamento dei vicini).
# Acqua: alla semina, se la cella e' sotto W_LOW, la si porta a W_RICH se in magazzino c'e' piu' di
# RICH, altrimenti a W_POOR; in attesa della crescita si porta la cella a W_WAIT.
#
# Differenza: l'interprete conta anche le istruzioni (if 1, chiamata 1, confronto 1, indice 1,
# for 1 a giro). La v5 spendeva ~70 tick di interprete per cella a strato (lista work[],
# statistiche, stampe); qui ~30. Su lb_rice_single.py la stessa pulizia ha dato -2.1 s.
# 32 droni, una colonna a testa.
# v1 (lb_rice_multi_v1.py) in gioco 1:53.712 (#2; #1 1:51.900). Stampe: l'ultimo strato parte a
# ~1.8M e ai 2M mancano 1300-1650 raccolti: tutto il 1o blocco (1024) piu' il 30-60% del 2o, ma la B
# scavava e ripiantava su tutte le celle; a fine run restavano ~690 acqua.
# v2: nell'ultimo strato la B scava e ripianta solo sulle prime celle che servono (+3 di margine),
#     le altre solo raccolta; con molta acqua in magazzino si annaffia gia' sotto W_LOW_RICH.

RICE = Entities.Rice
CLAY = Grounds.Clay
WATER = Items.Water
RI = Items.Rice
GOAL = 2000000
H_SKIP = 6
W_LOW = 0.1      # alla semina si annaffia solo sotto questo livello
W_POOR = 0.25    # ... fino a qui se l'acqua scarseggia
RICH = 100       # se in magazzino ce n'e' piu' di cosi' ...
W_RICH = 0.5     # ... fino a qui
W_LOW_RICH = 0.25  # con piu' di RICH in magazzino si annaffia gia' sotto questo livello
W_WAIT = 0.25    # in attesa della crescita
S = get_world_size()   # 32: un drone per colonna


def water_to(target):
	n = (target - get_water()) * 4
	m = n // 1
	if m < n:
		m += 1
	t = num_items(WATER) // 1
	if m > t:
		m = t
	if m >= 1:
		use_item(WATER, m)


def wplant():
	w = get_water()
	if w < W_LOW_RICH:
		if num_items(WATER) > RICH:
			water_to(W_RICH)
		elif w < W_LOW:
			water_to(W_POOR)


def wait_grown():
	water_to(W_WAIT)
	while not can_harvest():
		pass


def a2():
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	if plant(RICE):
		wplant()


def bb():
	# True = obiettivo raggiunto
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		wait_grown()
		harvest()
	else:
		if plant(RICE):
			wplant()
		return False
	if num_items(RI) >= GOAL:
		return True
	dig()
	if plant(RICE):
		wplant()
	return False


def aa():
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		wait_grown()
		harvest()
	else:
		return False
	return num_items(RI) >= GOAL


def worker(d):
	def fn():
		if d <= S // 2:
			for _ in range(d):
				move(East)
		else:
			for _ in range(S - d):
				move(West)
		while True:
			for _ in range(S):
				a2()
				move(North)
			# ultimo strato: dopo il 1o blocco servono ancora rem raccolti -> c2 solo sulle prime kneed celle
			kneed = S
			rem = GOAL - num_items(RI) - S * S * 128
			if rem < S * S * 128:
				kneed = rem / (S * 128) // 1 + 3
				if kneed > S:
					kneed = S
				if kneed < 0:
					kneed = 0
			for _ in range(kneed):
				if bb():
					clear()
					return
				move(North)
			for _ in range(S - kneed):
				if aa():
					clear()
					return
				move(North)
			for _ in range(S):
				if aa():
					clear()
					return
				move(North)
	return fn


def spawn_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(spawn_range_task(mid, hi))
		hi = mid
	worker(lo)()


def spawn_range_task(lo, hi):
	def fn():
		spawn_range(lo, hi)
	return fn


spawn_range(0, S)
