# Classifica Hay: 2e9 fieno, 32 droni.
# Simulatore: 1:50.0 (tua versione) -> 1:49.3.
# - il drone principale controlla il fieno dopo ogni harvest e chiude con clear(),
#   che elimina subito gli altri droni (Farm::RemoveSpawnedDrones): coda ~0.4 s -> ~0.02 s
# - gli altri droni non controllano mai il fieno (girano finche' clear() li rimuove)
# - nessuna riserva d'acqua: all'avvio l'acqua e' il collo di bottiglia
GOAL = 2000000000
W = 0.7

S = get_world_size()
BUSH = Entities.Bush
HAY = Items.Hay
WATER = Items.Water
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


def setup(b):
	i = b % 8
	bx = 4 * i
	by = (8 * (b // 8) + 4 * (i % 2)) % S
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
	return (bx, by), (bx + 1, by)


def farm_forever(west, east):
	while True:
		while not can_harvest():
			if get_water() < W and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		while True:
			while get_companion()[0] != BUSH:
				harvest()
			if get_companion()[1] != west:
				break
			harvest()
		move(West)

		while not can_harvest():
			if get_water() < W and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		while True:
			while get_companion()[0] != BUSH:
				harvest()
			if get_companion()[1] != east:
				break
			harvest()
		move(East)


def farm_main(west, east):
	while True:
		while not can_harvest():
			if get_water() < W and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		if num_items(HAY) >= GOAL:
			return
		while True:
			while get_companion()[0] != BUSH:
				harvest()
				if num_items(HAY) >= GOAL:
					return
			if get_companion()[1] != west:
				break
			harvest()
			if num_items(HAY) >= GOAL:
				return
		move(West)

		while not can_harvest():
			if get_water() < W and num_items(WATER) > 0:
				use_item(WATER)
		harvest()
		if num_items(HAY) >= GOAL:
			return
		while True:
			while get_companion()[0] != BUSH:
				harvest()
				if num_items(HAY) >= GOAL:
					return
			if get_companion()[1] != east:
				break
			harvest()
			if num_items(HAY) >= GOAL:
				return
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
	west, east = setup(lo)
	if lo == 0:
		farm_main(west, east)
		clear()
	else:
		farm_forever(west, east)


clear()
run_range(0, BLOCKS)
