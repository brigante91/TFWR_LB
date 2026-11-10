# Classifica Hay: 2e9 fieno, 32 droni. Variante "24/24 centrati" (1:49.519 di media) + v5.
# v5: il controllo del companion e' un indice di dizionario, BAD[get_companion()],
#     che costa 2 tick (test del while + get_companion) invece di 3 con "not in".
#     Un solo dizionario per le due erbe: tutte le 72 combinazioni possibili (3 tipi x celle dei
#     due rombi), True = da ritirare. Misurato in gioco: ~3.14 tentativi per raccolto buono,
#     quindi ~3 tick in meno per raccolto (~0.35 s).
GOAL = 2000000000
W = 0.68
W0 = 0.4
EARLY = 12

S = get_world_size()
BUSH = Entities.Bush
CARROT = Entities.Carrot
TREE = Entities.Tree
HAY = Items.Hay
WATER = Items.Water
BLOCKS = 32

# celle dei rombi di raggio 3 attorno alle due erbe, relative all'erba A
# (C a ovest di A, oppure C a est di A)
UNION_W = [
	(-4, 0), (-3, -1), (-3, 0), (-3, 1), (-2, -2), (-2, -1), (-2, 0), (-2, 1),
	(-2, 2), (-1, -3), (-1, -2), (-1, -1), (-1, 0), (-1, 1), (-1, 2), (-1, 3),
	(0, -3), (0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (0, 3), (1, -2),
	(1, -1), (1, 0), (1, 1), (1, 2), (2, -1), (2, 0), (2, 1), (3, 0)
]

UNION_E = [
	(-3, 0), (-2, -1), (-2, 0), (-2, 1), (-1, -2), (-1, -1), (-1, 0), (-1, 1),
	(-1, 2), (0, -3), (0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (0, 3),
	(1, -3), (1, -2), (1, -1), (1, 0), (1, 1), (1, 2), (1, 3), (2, -2),
	(2, -1), (2, 0), (2, 1), (2, 2), (3, -1), (3, 0), (3, 1), (4, 0)
]


def goto(tx, ty):
	dx = (tx - get_pos_x()) % S
	if dx <= 16:
		for _ in range(dx):
			move(East)
	else:
		for _ in range(S - dx):
			move(West)
	dy = (ty - get_pos_y()) % S
	if dy <= 16:
		for _ in range(dy):
			move(North)
	else:
		for _ in range(S - dy):
			move(South)


def bad_dict(ax, cx, y, offs):
	# True = companion da ritirare. Per l'erba A il companion non cade mai su A stessa,
	# per C mai su C: quindi un bush su A o su C e' sbagliato per l'altra erba.
	d = {}
	for o in offs:
		p = ((ax + o[0]) % S, (y + o[1]) % S)
		d[(CARROT, p)] = True
		d[(TREE, p)] = True
		d[(BUSH, p)] = False
	d[(BUSH, (ax % S, y))] = True
	d[(BUSH, (cx % S, y))] = True
	return d


def work_block(b):
	i = b % 8
	bx = 4 * i
	by = (8 * (b // 8) + 4 * (i % 2)) % S
	if i < 4:
		ex = bx
		d1 = East
		d2 = West
		ax = bx + 2
		cx = bx + 1
		offs = UNION_W
	else:
		ex = bx + 3
		d1 = West
		d2 = East
		ax = bx + 1
		cx = bx + 2
		offs = UNION_E

	goto(ex, (by + 7) % S)

	for _ in range(3):
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(d1)
		plant(BUSH)
		move(South)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(d2)
		plant(BUSH)
		move(South)

	plant(BUSH)
	move(South)
	plant(BUSH)
	move(d1)
	move(North)
	plant(BUSH)
	move(d1)
	plant(BUSH)
	move(d1)
	plant(BUSH)
	move(South)
	plant(BUSH)
	move(d2)

	return bad_dict(ax, cx, by, offs), d1, d2


def farm(BAD, d1, d2):
	for _ in range(EARLY):
		while not can_harvest():
			if get_water() < W0 and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		while BAD[get_companion()]:
			harvest()
		move(d2)
		while not can_harvest():
			if get_water() < W0 and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		while BAD[get_companion()]:
			harvest()
		move(d1)
	while True:
		while not can_harvest():
			if get_water() < W and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		while BAD[get_companion()]:
			harvest()
		move(d2)
		while not can_harvest():
			if get_water() < W and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		while BAD[get_companion()]:
			harvest()
		move(d1)


def farm_main(BAD, d1, d2):
	for _ in range(EARLY):
		while not can_harvest():
			if get_water() < W0 and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		while BAD[get_companion()]:
			harvest()
		move(d2)
		while not can_harvest():
			if get_water() < W0 and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		while BAD[get_companion()]:
			harvest()
		move(d1)
	while True:
		while not can_harvest():
			if get_water() < W and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		if num_items(HAY) >= GOAL:
			return
		while BAD[get_companion()]:
			harvest()
			if num_items(HAY) >= GOAL:
				return
		move(d2)
		while not can_harvest():
			if get_water() < W and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		if num_items(HAY) >= GOAL:
			return
		while BAD[get_companion()]:
			harvest()
			if num_items(HAY) >= GOAL:
				return
		move(d1)


def make_task(lo, hi):
	def fn():
		run_range(lo, hi)
	return fn


def run_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(make_task(mid, hi))
		hi = mid
	BAD, d1, d2 = work_block(lo)
	if lo == 0:
		farm_main(BAD, d1, d2)
		clear()
	else:
		farm(BAD, d1, d2)


run_range(0, BLOCKS)
