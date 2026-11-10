# Classifica Rice (2e6 riso, 32 droni, 32x32). v9 del 9 nov 2026. GENERATO da gen_rice.py: non
# modificare a mano, cambiare il generatore.
# Storia: lb_rice.py v5 1:57.01; lb_rice_multi v1 1:53.712; v2 1:51.13x di media (#1); v3 1:51.024
# su 4 run (cicli in linea, niente controllo dell'obiettivo negli strati normali).
# v4 = v3 con le passate srotolate (il for costa 1 tick a giro: -3 tick per cella a strato) e il
#     livello dell'acqua controllato prima di chiamare wplant() (-1 tick per semina).
# v4 in gioco ~1:50.97. v5: in A2 e nel caso comune della B niente "if" attorno a plant() (-1 tick
#     a semina; annaffiare una cella saltata e' innocuo). Il controllo dell'acqua nella B resta:
#     nel simulatore toglierlo costa +1.6 s.
# v6: acqua mirata nella B quando scarseggia (magazzino <= RICH). La B pianta a 0.18 s/cella e la A1
#     raccoglie a 0.07 s/cella, quindi la A1 raggiunge le piante giovani: le celle tirate sono le
#     ULTIME della colonna, ma prima l'acqua la prendevano le prime e il serbatoio si svuotava.
#     Ora con poca acqua la B annaffia solo le ultime TAILB celle (a 0.25); con molta acqua tutte
#     (a 0.5) come prima. Sim (haysim/rice/v2.py, BSCARCE/TAILB): 110.8 -> 109.4 s; con acqua
#     infinita 97.9, quindi le attese per l'acqua valgono ancora ~11 s.
# v7: niente piantagione di ripiego nella B. Una cella saltata in A2 (roccia dura) veniva piantata
#     nella B e nella A1 non era cresciuta: il drone aspettava fino a 7 s, i vicini iniziavano la
#     discesa accanto al suo riso e TUTTA la sua colonna crollava (visto in gioco: colonne intere
#     vuote e il drone una passata indietro). Il ripiego valeva 128 riso, il crollo ~30 raccolti.
#     Opzione GUARD (spenta, ~0.2 s per drone): in A2 prima di scendere aspetta finche' le celle
#     vicine a Est e Ovest hanno riso.
# In gioco: v6 media 1:51.135, v7 1:52.087 dopo 7 run, contro 1:50.97 della v5: l'acqua mirata in
#     coda (v6) non rende come nel simulatore. v8 = acqua della v5 (TAILB = 0, tutte le celle con
#     wplant) + niente ripiego nella B (v7). In gioco 1:51.091 su 12 run (= v5): il ripiego non
#     c'entrava. Diagnostica (lb_rice_diag.py): zero salti per durezza, ~1 cella vuota ogni tanto,
#     riso pieno (262k/strato); strati 20.3 / 17.3 / 13.7 / poi 12.75 s: ~12 s di attese nei primi
#     3 strati (acqua), poi solo lavoro.
# v9: PRE-SCAVO. Nei primi PRELAYERS strati, quando in A1 il drone deve aspettare la crescita su una
#     cella >= KMIN (coda della colonna, attesa di 3-5 s), torna alla cella 0, scava la discesa
#     dello strato dopo (i 14 blocchi) e pianta gia' le prime PREDIG celle, poi torna indietro.
#     La A2 successiva salta le celle gia' piantate: niente 14 scavi (-1 s) e la cella 0 arriva
#     alla B gia' matura. Costo: la cella 31 (adiacente alla 0 col wrap) e fino a 3 celle dei
#     vicini crollano (~0.5k riso). Sim con evaporazione (tarato sugli strati del gioco):
#     113.2 -> 112.3 s su 6 seed; con 8-12 celle o col controllo dei vicini tornano i crolli.
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
PREDIG = 4              # celle pre-scavate e piantate durante l'attesa in A1
PRELAYERS = 2           # solo nei primi strati (dopo non si aspetta piu')
KMIN = 20               # il pre-scavo scatta solo aspettando su una cella >= KMIN


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


def wplant_head():
	# B, celle in testa alla colonna: acqua solo se ce n'e' tanta
	if num_items(WATER) > RICH:
		water_to(W_RICH)


def predig(n):
	# dalla cella 32-n alla cella 0 (n mosse a Nord), pre-scava e pianta PREDIG celle, torna indietro
	for _ in range(n):
		move(North)
	for _ in range(PREDIG):
		while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
			dig()
		plant(RICE)
		if get_water() < W_LOW_RICH:
			wplant()
		move(North)
	for _ in range(n + PREDIG):
		move(South)


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
		L = 0
		pd = 0
		while True:
			L += 1
			pd = 0
			# A2: scendi all'argilla e pianta (32 celle srotolate)
			if get_entity_type() != RICE:
				while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
					dig()
				plant(RICE)
				if get_water() < W_LOW_RICH:
					wplant()
			move(North)
			if get_entity_type() != RICE:
				while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
					dig()
				plant(RICE)
				if get_water() < W_LOW_RICH:
					wplant()
			move(North)
			if get_entity_type() != RICE:
				while get_ground_type() != CLAY and get_hardness() <= H_SKIP:
					dig()
				plant(RICE)
				if get_water() < W_LOW_RICH:
					wplant()
			move(North)
			if get_entity_type() != RICE:
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
					if pd == 0 and L <= PRELAYERS:
						pd = 1
						predig(12)
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					if pd == 0 and L <= PRELAYERS:
						pd = 1
						predig(11)
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					if pd == 0 and L <= PRELAYERS:
						pd = 1
						predig(10)
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					if pd == 0 and L <= PRELAYERS:
						pd = 1
						predig(9)
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					if pd == 0 and L <= PRELAYERS:
						pd = 1
						predig(8)
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					if pd == 0 and L <= PRELAYERS:
						pd = 1
						predig(7)
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					if pd == 0 and L <= PRELAYERS:
						pd = 1
						predig(6)
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					if pd == 0 and L <= PRELAYERS:
						pd = 1
						predig(5)
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					if pd == 0 and L <= PRELAYERS:
						pd = 1
						predig(4)
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					if pd == 0 and L <= PRELAYERS:
						pd = 1
						predig(3)
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					if pd == 0 and L <= PRELAYERS:
						pd = 1
						predig(2)
					wait_grown()
					harvest()
				move(North)
				if can_harvest():
					harvest()
				elif get_entity_type() == RICE:
					if pd == 0 and L <= PRELAYERS:
						pd = 1
						predig(1)
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
