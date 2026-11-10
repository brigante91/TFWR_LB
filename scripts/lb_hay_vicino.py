# Test del metodo diverso dalle coppie.
# Un'erba per drone, anello di cespugli, acqua tenuta piena.
# Se il companion e' sul vicino (distanza 1) si va a piantarlo; altrimenti si rerolla.
# Le 32 erbe sono sulla griglia a passo 5: i vicini di un drone non cadono nel rombo di un altro.
# Incollare in un file del gioco e lanciarlo. Non e' caricato da solo da questa cartella.
GOAL = 2000000000
S = get_world_size()
BUSH = Entities.Bush
TREE = Entities.Tree
CARROT = Entities.Carrot
WATER = Items.Water
HAY = Items.Hay
SOIL = Grounds.Soil
PITCH = 5


def goto(tx, ty):
	dx = (tx - get_pos_x()) % S
	if dx > S // 2:
		dx = dx - S
	dy = (ty - get_pos_y()) % S
	if dy > S // 2:
		dy = dy - S
	if dx > 0:
		for _ in range(dx):
			move(East)
	elif dx < 0:
		for _ in range(-dx):
			move(West)
	if dy > 0:
		for _ in range(dy):
			move(North)
	elif dy < 0:
		for _ in range(-dy):
			move(South)


def go(dx, dy):
	if dx > 0:
		for _ in range(dx):
			move(East)
	elif dx < 0:
		for _ in range(-dx):
			move(West)
	if dy > 0:
		for _ in range(dy):
			move(North)
	elif dy < 0:
		for _ in range(-dy):
			move(South)


def plant_bush():
	if get_entity_type() == BUSH:
		return
	if get_ground_type() == SOIL:
		till()
	plant(BUSH)


def plant_kind(kind):
	here = get_entity_type()
	if here == kind:
		return True
	if kind == CARROT:
		if get_ground_type() != SOIL:
			till()
		return plant(CARROT)
	if get_ground_type() == SOIL:
		till()
	return plant(kind)


def ring(bx, by, mem):
	# scansiona il rombo di raggio 3 e ci pianta cespugli
	y = -3
	while y <= 3:
		x = -3
		while x <= 3:
			if abs(x) + abs(y) <= 3 and (x != 0 or y != 0):
				px = (bx + x) % S
				py = (by + y) % S
				goto(px, py)
				plant_bush()
				put(mem, px, py, BUSH)
			x = x + 1
		y = y + 1
	goto(bx, by)


def refill():
	n = 0
	while n < 4 and get_water() < 0.98:
		if not use_item(WATER):
			return
		n = n + 1


def at(mem, x, y):
	key = (x, y)
	if key in mem:
		return mem[key]
	return None


def put(mem, x, y, kind):
	mem[(x, y)] = kind


def fix(bx, by, mem):
	while get_entity_type() != None:
		c = get_companion()
		if c == None:
			return
		kind = c[0]
		p = c[1]
		x = p[0]
		y = p[1]
		if at(mem, x, y) == kind:
			return
		dx = x - bx
		if dx > S // 2:
			dx = dx - S
		elif dx < -S // 2:
			dx = dx + S
		dy = y - by
		if dy > S // 2:
			dy = dy - S
		elif dy < -S // 2:
			dy = dy + S
		if abs(dx) + abs(dy) == 1:
			go(dx, dy)
			ok = plant_kind(kind)
			if not ok:
				if get_ground_type() == SOIL:
					till()
				plant(BUSH)
				put(mem, x, y, BUSH)
				ok = False
			go(-dx, -dy)
			if ok:
				put(mem, x, y, kind)
				return
		if not harvest():
			return


def work(b):
	bx = PITCH * (b % 6)
	by = PITCH * (b // 6)
	mem = {}
	ring(bx, by, mem)
	main = b == 0
	n = 0
	while True:
		while not can_harvest():
			if get_water() < 0.98:
				use_item(WATER)
		harvest()
		refill()
		fix(bx, by, mem)
		if main:
			n = n + 1
			if n % 40 == 0:
				quick_print(get_time(), num_items(HAY))
			if num_items(HAY) >= GOAL:
				clear()
				return


def run_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(run_range, mid, hi)
		hi = mid
	work(lo)


run_range(0, 32)
