EXTRA = 150000000  # carote da produrre in questa esecuzione
W = 0.6

S = get_world_size()
BUSH = Entities.Bush
CARROT = Entities.Carrot
COLS = S // 4
ROWS = S // 8
BLOCKS = min(max_drones(), COLS * ROWS)
TARGET = num_items(Items.Carrot) + EXTRA


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
	i = b % COLS
	j = b // COLS
	return 4 * i, (8 * j + 4 * (i % 2)) % S


def reroll(avoid):
	c, pos = get_companion()
	while c != BUSH or pos == avoid:
		old = (c, pos)
		plant(CARROT)  # se funziona sopra una carota acerba, costa un'azione sola
		c, pos = get_companion()
		if (c, pos) == old:
			harvest()  # altrimenti: togli la carota acerba e ripianta
			plant(CARROT)
			c, pos = get_companion()


def carrot_cell(avoid):
	while not can_harvest():
		if get_water() < W and num_items(Items.Water) > 16:
			use_item(Items.Water)
	harvest()
	plant(CARROT)
	reroll(avoid)


def work_block(b):
	bx, by = block_origin(b)

	# bush su tutto il blocco tranne le due celle carota (serpentina come per il fieno)
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

	# celle carota: (bx+1, by) e (bx, by)
	west = (bx, by)
	east = (bx + 1, by)
	if get_ground_type() != Grounds.Soil:
		till()
	plant(CARROT)
	reroll(west)
	move(West)
	if get_ground_type() != Grounds.Soil:
		till()
	plant(CARROT)
	reroll(east)
	move(East)

	while num_items(Items.Carrot) < TARGET:
		carrot_cell(west)
		move(West)
		carrot_cell(east)
		move(East)


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
quick_print("fattoria", S, "drone", max_drones(), "blocchi", BLOCKS, "carote ora", num_items(Items.Carrot))
run_range(0, BLOCKS)