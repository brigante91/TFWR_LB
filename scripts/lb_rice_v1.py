# Classifica Rice (2e6 riso, tutti i droni) e Rice_Single (1e5, 1 drone, 8x8). v1 dell'8 nov 2026.
# Lo stesso file va bene per tutte e due: obiettivo, droni e percorso si scelgono da soli.
#
# Regole (decompilato del 6 nov + asset):
# - il riso cresce solo su Grounds.Clay; piantato, il terreno diventa Rice_Terrace; quando e'
#   maturo diventa Dry_Rice_Terrace e li' non si ripianta: dig() toglie il blocco secco e sotto c'e'
#   di nuovo argilla (la classifica e' fatta solo di strati d'argilla).
# - crescita 6 s * U(0.8, 1.2) / (1 + 4 * acqua); resa 2^(livello-1) = 128 a raccolto (riso liv. 8):
#   15625 raccolti per Rice, 782 per Rice_Single.
# - dig() su una pianta la distrugge SENZA resa: prima harvest(), poi dig(); harvest() su riso
#   non maturo lo distrugge: prima can_harvest().
# - dig dell'argilla (durezza 2): 2 / 1.5^livello_trapano secondi, circa 2-3 azioni.
# - crolli: una colonna crolla se un vicino e' piu' profondo di 4 blocchi (stabilita' argilla 3).
#   Ogni cella viene scavata una volta per passata, quindi le colonne scendono insieme.
# - acqua: il serbatoio da' 25.6 unita'/s per tutto il campo, 0.25 di acqua a unita', evapora
#   circa 1%/s. Basta pochissima acqua (w >= 0.07) perche' la crescita stia sotto la passata.
#
# Schema: ogni drone ha un blocco di colonne e lo percorre in ciclo. Per ogni cella:
# aspetta che sia matura (annaffiando se serve), harvest, dig, plant, eventuale acqua, move.
# Simulato (32 droni, 32x32): senza acqua ~114 s, con acqua sotto soglia ~100 s.
# Rice_Single: la passata da 64 celle dura ~13 s, il riso e' sempre maturo: niente acqua.
# A obiettivo raggiunto il drone che se ne accorge chiama clear() (ferma tutti gli altri).

S = get_world_size()
D = min(max_drones(), S)
if max_drones() <= 1:
	GOAL = 100000
else:
	GOAL = 2000000

RICE = Entities.Rice
CLAY = Grounds.Clay
WATER = Items.Water
RICE_ITEM = Items.Rice

W_TH = 0.07      # annaffia se l'acqua della cella e' sotto questa soglia
MAX_DIG = 40     # sicurezza: scavi massimi per trovare l'argilla


def cols_of(d):
	return (d * S) // D, ((d + 1) * S) // D


def make_path(d):
	# ciclo sulle colonne [x0, x1): dirs[k] = mossa dopo il passo k, work[k] = cella da lavorare
	x0, x1 = cols_of(d)
	k = x1 - x0
	dirs = []
	work = []
	if k == 1:
		for _ in range(S):
			dirs.append(North)
			work.append(True)
		return dirs, work
	# serpentina: colonne pari verso Nord, dispari verso Sud
	for c in range(k):
		for _ in range(S - 1):
			if c % 2 == 0:
				dirs.append(North)
			else:
				dirs.append(South)
			work.append(True)
		dirs.append(East)
		work.append(True)
	# ritorno a (x0, 0) dopo l'ultima cella
	if k == S and k % 2 == 0:
		return dirs, work      # l'ultima East fa il giro (wrap) fino a (x0, 0)
	dirs[len(dirs) - 1] = West
	for _ in range(k - 2):
		dirs.append(West)
		work.append(False)
	if k % 2 == 1:
		dirs.append(North)     # finiti in alto (y = S-1): wrap a y = 0
		work.append(False)
	return dirs, work


def goto(tx, ty):
	x = get_pos_x()
	y = get_pos_y()
	dx = (tx - x) % S
	if dx <= S // 2:
		for _ in range(dx):
			move(East)
	else:
		for _ in range(S - dx):
			move(West)
	dy = (ty - y) % S
	if dy <= S // 2:
		for _ in range(dy):
			move(North)
	else:
		for _ in range(S - dy):
			move(South)


def dig_to_clay():
	n = 0
	while get_ground_type() != CLAY and n < MAX_DIG:
		dig()
		n += 1
	return plant(RICE)


def worker(d):
	def fn():
		x0, x1 = cols_of(d)
		dirs, work = make_path(d)
		n = len(dirs)
		water_plant = (x1 - x0) * S < 40
		goto(x0, 0)
		# prima passata: scava fino all'argilla e pianta
		for k in range(n):
			if work[k]:
				if get_entity_type() != RICE:
					dig_to_clay()
				if water_plant and get_water() < W_TH and num_items(WATER) >= 1:
					use_item(WATER)
			move(dirs[k])
		while True:
			for k in range(n):
				if work[k]:
					if get_entity_type() == RICE:
						if not can_harvest():
							if get_water() < W_TH and num_items(WATER) >= 1:
								use_item(WATER)
							while not can_harvest():
								pass
						harvest()
						if num_items(RICE_ITEM) >= GOAL:
							clear()
							return
						dig()
						if not plant(RICE):
							dig_to_clay()
					else:
						dig_to_clay()
					if water_plant and get_water() < W_TH and num_items(WATER) >= 1:
						use_item(WATER)
				move(dirs[k])
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


spawn_range(0, D)
