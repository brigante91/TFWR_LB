# Classifica Rice (2e6 riso, 32 droni, 32x32). v5 dell'8 nov 2026. GENERATO da gen_rice.py: non
# modificare a mano, cambiare il generatore.
# Storia: lb_rice.py v5 1:57.01; lb_rice_multi v1 1:53.712; v2 1:51.13x di media (#1); v3 1:51.024
# su 4 run (cicli in linea, niente controllo dell'obiettivo negli strati normali).
# v4 = v3 con le passate srotolate (il for costa 1 tick a giro: -3 tick per cella a strato) e il
#     livello dell'acqua controllato prima di chiamare wplant() (-1 tick per semina).
# v4 in gioco ~1:50.97. v5: in A2 e nel caso comune della B niente "if" attorno a plant() (-1 tick
#     a semina; annaffiare una cella saltata e' innocuo). Il controllo dell'acqua nella B resta:
#     nel simulatore toglierlo costa +1.6 s.
#
# Schema: ogni drone ha una colonna di 32 celle e la percorre verso Nord (wrap). Per strato:
#   A2: scendi all'argilla e pianta;  B: raccogli, scava la terrazza secca, pianta sul 2o blocco;
#   A1: raccogli il 2o blocco (la terrazza secca la toglie il crollo nella A2 dopo).
# Celle con durezza > H_SKIP saltate (le abbassa il trascinamento dei vicini).
# Acqua alla semina: sotto W_LOW_RICH si porta a W_RICH se in magazzino ce n'e' piu' di RICH,
# altrimenti sotto W_LOW si porta a W_POOR; in attesa della crescita si porta a W_WAIT.
# Ultimo strato (mancano meno di un blocco intero + MARGIN prima della B): B scava e ripianta solo
# sulle prime kneed celle, controllo dell'obiettivo a ogni raccolto.

RICE = Entities.Rice
CLAY = Grounds.Clay
WATER = Items.Water
RI = Items.Rice
GOAL = 2000000
H_SKIP = 6
W_LOW = 0.1
W_POOR = 0.25
RICH = 100
W_RICH = 0.5
W_LOW_RICH = 0.25
W_WAIT = 0.25
S = get_world_size()   # 32: un drone per colonna
LAYER = S * S * 128     # riso di un blocco d'argilla su tutto il campo
MARGIN = 200 * 128      # sicurezza sul passaggio alla versione con i controlli


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


def bb():
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


def final_layer(rem):
	# ultimo strato: c2 solo sulle prime kneed celle, controlli a ogni raccolto. True = obiettivo
	kneed = S
	if rem < LAYER:
		kneed = rem // (S * 128) + 3
		if kneed > S:
			kneed = S
		if kneed < 0:
			kneed = 0
	for _ in range(kneed):
		if bb():
			return True
		move(North)
	for _ in range(S - kneed):
		if aa():
			return True
		move(North)
	for _ in range(S):
		if aa():
			return True
		move(North)
	return False

def worker(d):
	def fn():
		if d <= S // 2:
			for _ in range(d):
				move(East)
		else:
			for _ in range(S - d):
				move(West)
		while True:
			# A2: scendi all'argilla e pianta (32 celle srotolate)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
				dig()
			plant(RICE)
			if get_water() < W_LOW_RICH:
				wplant()
			move(North)
			rem = GOAL - num_items(RI) - LAYER
			if rem > LAYER + MARGIN:
				# strato normale: B e A1 senza controlli dell'obiettivo (srotolate)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
					dig()
					plant(RICE)
					if get_water() < W_LOW_RICH:
						wplant()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
					dig()
					if plant(RICE):
						wplant()
				elif plant(RICE):
					wplant()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					wait_grown()
					harvest()
				move(North)
			elif final_layer(rem):
				clear()
				return
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
