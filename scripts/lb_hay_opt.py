# Classifica Hay: 2.000.000.000 fieno, 32 drone.
# Ottimizzato per rompere il muro dell'1:50 e arrestarsi al traguardo esatto.
GOAL = 2000000000
W = 0.9

S = get_world_size()
BUSH = Entities.Bush
BLOCKS = 32


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


def block_origin(b):
	i = b % 8
	j = b // 8
	return 4 * i, (8 * j + 4 * (i % 2)) % S


def work_block(b):
	bx, by = block_origin(b)
	goto(bx, by + 7)
	for k in range(7):
		if k % 2 == 0:
			d = East
		else:
			d = West
		for _ in range(3):
			plant(BUSH)
			move(d)
		plant(BUSH)
		move(South)
	plant(BUSH)
	move(West)
	plant(BUSH)
	move(West)

	west = (bx, by)
	east = (bx + 1, by)

	goto(bx, by)
	siamo_a_est = False

	c, pos = get_companion()
	while c != BUSH or (pos != west and pos != east):
		harvest()
		c, pos = get_companion()

	while True:
		# Controllo di interruzione globale per tutti i droni
		if num_items(Items.Hay) >= GOAL:
			break

		if get_water() < W and num_items(Items.Water) > 16:
			use_item(Items.Water, 4)

		while not can_harvest():
			# Gestione della sicurezza nel loop di attesa
			if num_items(Items.Hay) >= GOAL:
				break

		# Secondo controllo prima del raccolto per evitare sforamenti asincroni
		if num_items(Items.Hay) >= GOAL:
			break

		harvest()
		c, pos = get_companion()

		while c != BUSH or (pos != west and pos != east):
			harvest()
			c, pos = get_companion()

		if pos == east and not siamo_a_est:
			move(East)
			siamo_a_est = True
		elif pos == west and siamo_a_est:
			move(West)
			siamo_a_est = False


def make_task(lo, hi):
	def fn():
		run_range(lo, hi)
	return fn


def run_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(make_task(mid, hi))
		hi = mid
	work_block(lo)


clear()
run_range(0, BLOCKS)
