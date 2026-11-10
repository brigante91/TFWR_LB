# Strategia Cactus 33.554.432 - v4 (Ottimizzata per il minor tempo possibile)
GOAL = 33554432
K_REROLL = 8
SLACK = 1
SIG_W = 8
SIG_GO = 60
S = get_world_size()
CACTUS = Entities.Cactus
SOIL = Grounds.Soil
WATER = Items.Water
DIAG = 2 * S - 1
N_WORK = S - 1


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


# Shaker sort (ottimizzato come nel tuo originale)
def shaker(fwd, back):
	lo = 0
	hi = S - 1
	while lo < hi:
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


def column(x):
	# il drone e' in (x, 0)
	for _ in range(S):
		if get_ground_type() != SOIL:
			till()
		plant(CACTUS)
		move(North)
		
	# Banda diagonale
	LO = []
	HI = []
	for y in range(S):
		t = ((x + y) * 10) // DIAG
		LO.append(t - SLACK)
		HI.append(t + SLACK)
		
	for _ in range(K_REROLL):
		bad = 0
		for y in range(S):
			m = measure()
			if (m < LO[y] or m > HI[y]) and can_harvest():
				till()
				till()
				plant(CACTUS)
				bad += 1
			move(North)
		if bad == 0:
			break
	shaker(North, South)


def signal():
	while not use_item(WATER, SIG_W):
		pass


def wait_go(off):
	soglia = N_WORK * SIG_W + SIG_GO - SIG_W
	while True:
		exp = (get_time() / 0.0390625) // 1 - off
		if exp - num_items(WATER) >= soglia:
			return


def worker(x):
	def fn():
		off = (get_time() / 0.0390625) // 1 - num_items(WATER)
		goto(x, 0)
		column(x)
		signal()
		wait_go(off)
		goto(0, x)
		shaker(East, West)
	return fn


clear()
OFF = (get_time() / 0.0390625) // 1 - num_items(WATER)
handles = []
for x in range(1, S):
	handles.append(spawn_drone(worker(x)))

column(0)
# Il main aspetta che tutti i worker abbiano mandato il segnale
while True:
	exp = (get_time() / 0.0390625) // 1 - OFF
	spent = exp - num_items(WATER)
	if (spent + 5) // SIG_W >= N_WORK:
		break

while not use_item(WATER, SIG_GO):
	pass

goto(0, 0)
shaker(East, West)

for h in handles:
	wait_for(h)

while not can_harvest():
	pass
harvest()
quick_print("Harvest a", get_time(), "cactus", num_items(Items.Cactus))