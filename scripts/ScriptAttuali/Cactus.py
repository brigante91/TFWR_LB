EXTRA = 950000000  # cactus da produrre
BAND = 2           # tolleranza attorno al valore atteso (9 = nessun reroll)
MAX_TRIES = 15     # tentativi massimi di reroll per cella

S = get_world_size()
CACTUS = Entities.Cactus
TARGET = num_items(Items.Cactus) + EXTRA


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


def shaker(fwd, back):
	# Cocktail sort sulla linea; il drone parte dalla casella 0.
	# Dopo ogni passata restringe [lo, hi] alla zona ancora da ordinare.
	lo = 0
	hi = S - 1
	while lo < hi:
		# passata in avanti: porta i valori grandi verso hi
		last = lo
		cur = measure()
		k = lo
		while k < hi:
			nxt = measure(fwd)
			if cur > nxt:
				swap(fwd)
				last = k
			else:
				cur = nxt
			move(fwd)
			k += 1
		for _ in range(hi - last):
			move(back)
		hi = last
		if lo >= hi:
			return
		# passata all'indietro: porta i valori piccoli verso lo
		last = hi
		cur = measure()
		k = hi
		while k > lo:
			nxt = measure(back)
			if cur < nxt:
				swap(back)
				last = k
			else:
				cur = nxt
			move(back)
			k -= 1
		for _ in range(last - lo):
			move(fwd)
		lo = last


def plant_near(t):
	# pianta un cactus e lo ripianta finche' la dimensione e' vicina a t
	plant(CACTUS)
	v = measure()
	tries = 0
	while (v < t - BAND or v > t + BAND) and tries < MAX_TRIES:
		harvest()
		if get_entity_type() != None:
			return  # non si toglie: lo tengo, ci pensa l'ordinamento
		plant(CACTUS)
		v = measure()
		tries += 1


def column(x):
	goto(x, 0)
	for y in range(S):
		if get_ground_type() != Grounds.Soil:
			till()
		if get_entity_type() == None:
			plant_near((9 * (x + y) + 31) // 62)  # valore atteso 0..9, cresce verso nord-est
		move(North)
	shaker(North, South)


def row(y):
	goto(0, y)
	shaker(East, West)


def make_column(x):
	def fn():
		column(x)
	return fn


def make_row(y):
	def fn():
		row(y)
	return fn


def run_phase(maker, own):
	handles = []
	for i in range(1, S):
		h = spawn_drone(maker(i))
		if h != None:
			handles.append(h)
	own(0)
	for h in handles:
		wait_for(h)


clear()
quick_print("fattoria", S, "drone", max_drones(), "BAND", BAND, "cactus ora", num_items(Items.Cactus))

t0 = get_time()
while num_items(Items.Cactus) < TARGET:
	run_phase(make_column, column)  # semina quasi in ordine + ordina le colonne
	run_phase(make_row, row)        # ordina le righe
	goto(0, 0)
	while not can_harvest():
		pass
	before = num_items(Items.Cactus)
	harvest()
	quick_print("raccolto:", num_items(Items.Cactus) - before, "totale", num_items(Items.Cactus), "secondi ciclo", get_time() - t0)
	t0 = get_time()