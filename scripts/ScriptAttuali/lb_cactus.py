# Cactus Leaderboard 32x32 - Ottimizzato
GOAL = 33554432
K = 3          # 3 passate bastano con SLACK=2
SLACK = 2      # Finestra al 50% di accettazione: elimina 4+ s di attesa crescita
S = get_world_size()
CACTUS = Entities.Cactus
SOIL = Grounds.Soil
DIAG = 2 * S - 1


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
	lo = 0
	hi = S - 1
	while lo < hi:
		swapped = False
		last = lo
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

		# Se la passata in avanti non ha trovato inversioni, la sequenza e' ordinata
		if not swapped:
			return

		for _ in range(hi - last):
			move(back)
		hi = last
		if lo >= hi:
			return

		swapped = False
		last = hi
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

		for _ in range(last - lo):
			move(fwd)
		lo = last


def column_task(x):
	goto(x, 0)
	for _ in range(S):
		if get_ground_type() != SOIL:
			till()
		plant(CACTUS)
		move(North)

	LO = []
	HI = []
	for y in range(S):
		t = ((x + y) * 10) // DIAG
		LO.append(t - SLACK)
		HI.append(t + SLACK)

	for _ in range(K):
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


def row_task(y):
	goto(0, y)
	shaker(East, West)


clear()

# Fase 1: Ordinamento colonne in parallelo
col_handles = []
for x in range(1, S):
	col_handles.append(spawn_drone(column_task, x))
column_task(0)

for h in col_handles:
	wait_for(h)

# Fase 2: Ordinamento righe in parallelo (partenza da x=0, tragitto medio: 8 passi)
row_handles = []
for y in range(1, S):
	row_handles.append(spawn_drone(row_task, y))
row_task(0)

for h in row_handles:
	wait_for(h)

# Raccolta finale istantanea
while not can_harvest():
	pass
harvest()
quick_print("Completato in:", get_time(), "Cactus:", num_items(Items.Cactus))