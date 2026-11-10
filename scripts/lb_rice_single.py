# Classifica Rice_Single (1e5 riso, 1 drone, 8x8). v4 dell'8 nov 2026. GENERATO da gen_rice.py:
# non modificare a mano, cambiare il generatore.
# Storia: lb_rice.py v7 2:29.1; lb_rice_single v1 2:27.208 (#4); v2 2:26 (ultimo strato ad anello);
# versione inline dell'utente (sweep_a2/bb/aa) stimata -0.3/-0.5 s.
# v3 = versione inline con le passate srotolate (il for costa 1 tick a giro: -3 tick per cella a
#     strato) e l'acqua controllata prima di chiamare water_full() (-1 tick per semina).
# v4: in A2 e nel caso comune della B niente "if" attorno a plant() (-1 tick a semina).
#
# Schema: per strato tre passate a serpentina sulle 64 celle
#   A2: scendi all'argilla e pianta;  B: raccogli, scava la terrazza secca, pianta sul 2o blocco;
#   A1: raccogli il 2o blocco (la terrazza secca la toglie il crollo nella A2 dopo).
# Acqua: alla semina, se la cella e' sotto S_LOW, la si riempie a 1.0 (circa una volta per cella).
# Ultimo strato: si piantano solo le colonne che servono, si torna a (0, 0) e si raccoglie nello
# stesso ordine della semina. Controllo dell'obiettivo a fine colonna nelle passate normali (la run
# finisce sempre nell'ultimo strato) e a ogni raccolto nell'ultimo strato.

RICE = Entities.Rice
CLAY = Grounds.Clay
WATER = Items.Water
RI = Items.Rice
GOAL = 100000
H_SKIP = 6
S_LOW = 0.15
S = get_world_size()
HALF = S // 2
STEPS = S - 1


def water_full():
	n = (1.0 - get_water()) * 4 // 1
	if n >= 1:
		t = num_items(WATER) // 1
		if n > t:
			n = t
		if n >= 1:
			use_item(WATER, n)


def goto0():
	x = get_pos_x()
	y = get_pos_y()
	if x <= HALF:
		for _ in range(x):
			move(West)
	else:
		for _ in range(S - x):
			move(East)
	if y <= HALF:
		for _ in range(y):
			move(South)
	else:
		for _ in range(S - y):
			move(North)

def sweep_a2():
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(East)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(East)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(East)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(East)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(East)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(East)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(North)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(East)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(South)
	while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
		dig()
	plant(RICE)
	if get_water() < S_LOW:
		water_full()
	move(East)


def sweep_bb():
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(North)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	move(South)
	if can_harvest():
		harvest()
		dig()
		plant(RICE)
		if get_water() < S_LOW:
			water_full()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
		dig()
		if plant(RICE):
			if get_water() < S_LOW:
				water_full()
	else:
		plant(RICE)
	if num_items(RI) >= GOAL:
		return True
	move(East)
	return False


def sweep_aa():
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(North)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	if num_items(RI) >= GOAL:
		return True
	move(East)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	move(South)
	if can_harvest():
		harvest()
	elif get_entity_type() == RICE:
		while not can_harvest():
			pass
		harvest()
	if num_items(RI) >= GOAL:
		return True
	move(East)
	return False


def final_round(cols):
	for c in range(cols):
		for _ in range(STEPS):
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			if plant(RICE):
				water_full()
			if c % 2 == 0:
				move(North)
			else:
				move(South)
		while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
			dig()
		if plant(RICE):
			water_full()
		move(East)
	goto0()
	for c in range(cols):
		for _ in range(STEPS):
			if can_harvest():
				harvest()
				if num_items(RI) >= GOAL:
					return True
			elif get_entity_type() == RICE:
				while not can_harvest():
					pass
				harvest()
				if num_items(RI) >= GOAL:
					return True
			if c % 2 == 0:
				move(North)
			else:
				move(South)
		if can_harvest():
			harvest()
			if num_items(RI) >= GOAL:
				return True
		elif get_entity_type() == RICE:
			while not can_harvest():
				pass
			harvest()
			if num_items(RI) >= GOAL:
				return True
		move(East)
	return False


while True:
	rem = GOAL - num_items(RI)
	c = (rem + 128 + S * 128 - 1) // (S * 128)
	if c < S:
		if final_round(c):
			clear()
			break
		goto0()
	sweep_a2()
	if sweep_bb():
		clear()
		break
	if sweep_aa():
		clear()
		break
