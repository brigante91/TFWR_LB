# Classifica Cactus: 33.554.432, un 32x32 ordinato.
#
# La taglia resta sulla cella finche' il cactus non e' cresciuto: niente reroll sul seme.
# Si ordina con lo shaker (uscite anticipate). 32 droni, uno per colonna; gli stessi
# passano alle righe senza rinascere. Chi finisce prima va gia' all'inizio della sua riga
# mentre gli altri chiudono la colonna.
#
# Il tempo e' la somma dei due massimi, non la media: circa 27 s la colonna piu' lenta
# (piantare compreso) e circa 18 s la riga piu' lenta. Sotto i 20 s non ci si arriva:
# quelle coppie fuori posto vanno scambiate una a una, e una riga non si puo' toccare
# prima che tutte le colonne siano a posto.
GOAL = 33554432
S = get_world_size()
N_WORK = S - 1
SIG_W = 8
SIG_GO = 60
CACTUS = Entities.Cactus
SOIL = Grounds.Soil
WATER = Items.Water
DT = 0.0390625


def goto(tx, ty):
	x = get_pos_x()
	y = get_pos_y()
	dx = (tx - x) % S
	if dx > S // 2:
		dx = dx - S
	while dx > 0:
		move(East)
		dx -= 1
	while dx < 0:
		move(West)
		dx += 1
	dy = (ty - y) % S
	if dy > S // 2:
		dy = dy - S
	while dy > 0:
		move(North)
		dy -= 1
	while dy < 0:
		move(South)
		dy += 1


def shaker(fwd, back):
	lo = 0
	hi = S - 1
	while lo < hi:
		last = lo
		swapped = False
		cur = measure()
		k = lo
		while k < hi:
			nxt = measure(fwd)
			if cur > nxt:
				swap(fwd)
				last = k
				swapped = True
			else:
				cur = nxt
			move(fwd)
			k += 1
		if not swapped:
			return
		steps = hi - last
		while steps > 0:
			move(back)
			steps -= 1
		hi = last
		if lo >= hi:
			return
		last = hi
		swapped = False
		cur = measure()
		k = hi
		while k > lo:
			nxt = measure(back)
			if cur < nxt:
				swap(back)
				last = k
				swapped = True
			else:
				cur = nxt
			move(back)
			k -= 1
		if not swapped:
			return
		steps = last - lo
		while steps > 0:
			move(fwd)
			steps -= 1
		lo = last


def plant_line():
	y = 0
	while y < S:
		if get_ground_type() != SOIL:
			till()
		plant(CACTUS)
		move(North)
		y += 1


def spent(off):
	return (get_time() / DT) // 1 - off - num_items(WATER)


def column_then_row(x):
	off = (get_time() / DT) // 1 - num_items(WATER)
	goto(x, 0)
	plant_line()
	shaker(North, South)
	goto(0, x)
	while not use_item(WATER, SIG_W):
		pass
	need = N_WORK * SIG_W + SIG_GO - SIG_W
	while spent(off) < need:
		pass
	shaker(East, West)


def launch(x):
	def fn():
		column_then_row(x)
	return fn


clear()
OFF = (get_time() / DT) // 1 - num_items(WATER)
hs = []
x = 1
while x < S:
	hs.append(spawn_drone(launch(x)))
	x += 1

plant_line()
shaker(North, South)
goto(0, 0)
while spent(OFF) < N_WORK * SIG_W - 1:
	pass
while not use_item(WATER, SIG_GO):
	pass
shaker(East, West)

i = 0
while i < N_WORK:
	wait_for(hs[i])
	i += 1

while not can_harvest():
	pass
harvest()
quick_print("Cactus", num_items(Items.Cactus), "in", get_time())
