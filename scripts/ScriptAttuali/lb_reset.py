# Fastest Reset — da 1x1 a Unlocks.Leaderboard.
# Lancia: leaderboard_run(Leaderboards.Fastest_Reset, "lb_reset", 1000000)
# Ordine unlock ispirato al top pubblico (~33m). Completa la run; non e' un WR.

ws = 1
CELL = None
PETAL_TARGET = 15
LEFT = {North: West, East: North, South: East, West: South}
RIGHT = {North: East, East: South, South: West, West: North}
OPP = {North: South, East: West, South: North, West: East}

ORDER = [
	Unlocks.Speed, Unlocks.Plant, Unlocks.Expand, Unlocks.Expand, Unlocks.Speed,
	Unlocks.Carrots, Unlocks.Grass, Unlocks.Trees, Unlocks.Trees, Unlocks.Expand,
	Unlocks.Carrots, Unlocks.Speed, Unlocks.Expand, Unlocks.Watering, Unlocks.Watering,
	Unlocks.Carrots, Unlocks.Grass, Unlocks.Sunflowers, Unlocks.Fertilizer, Unlocks.Watering,
	Unlocks.Speed, Unlocks.Pumpkins, Unlocks.Watering, Unlocks.Polyculture, Unlocks.Speed,
	Unlocks.Expand, Unlocks.Fertilizer, Unlocks.Mazes, Unlocks.Megafarm, Unlocks.Trees,
	Unlocks.Trees, Unlocks.Carrots, Unlocks.Watering, Unlocks.Pumpkins, Unlocks.Pumpkins,
	Unlocks.Expand, Unlocks.Cactus, Unlocks.Dinosaurs, Unlocks.Dinosaurs, Unlocks.Polyculture,
	Unlocks.Mazes, Unlocks.Mazes, Unlocks.Megafarm, Unlocks.Megafarm, Unlocks.Grass,
	Unlocks.Trees, Unlocks.Fertilizer, Unlocks.Fertilizer, Unlocks.Watering, Unlocks.Carrots,
	Unlocks.Carrots, Unlocks.Pumpkins, Unlocks.Pumpkins, Unlocks.Expand, Unlocks.Megafarm,
	Unlocks.Cactus, Unlocks.Cactus, Unlocks.Dinosaurs, Unlocks.Dinosaurs, Unlocks.Dinosaurs,
	Unlocks.Mazes, Unlocks.Leaderboard,
]


def refresh_ws():
	global ws
	ws = get_world_size()


def goto(x, y):
	n = get_world_size()
	dx = (x - get_pos_x()) % n
	if dx <= n // 2:
		for _ in range(dx):
			move(East)
	else:
		for _ in range(n - dx):
			move(West)
	dy = (y - get_pos_y()) % n
	if dy <= n // 2:
		for _ in range(dy):
			move(North)
	else:
		for _ in range(n - dy):
			move(South)


def water_here():
	if num_unlocked(Unlocks.Watering) > 0:
		while get_water() < 0.5 and num_items(Items.Water) > 0:
			use_item(Items.Water)


def fert_here():
	if num_unlocked(Unlocks.Fertilizer) > 0:
		while not can_harvest() and num_items(Items.Fertilizer) > 0:
			use_item(Items.Fertilizer)


def sow(entity, do_water):
	et = get_entity_type()
	if can_harvest() or (et != None and et != entity and et != Entities.Dead_Pumpkin):
		harvest()
	if entity == Entities.Grass or entity == Entities.Bush or entity == Entities.Tree:
		if get_ground_type() != Grounds.Grassland:
			till()
	else:
		if get_ground_type() != Grounds.Soil:
			till()
	if do_water:
		water_here()
	if entity != Entities.Grass and get_entity_type() != entity:
		plant(entity)


def wait_drones(handles):
	for h in handles:
		if h != None:
			wait_for(h)


def col_runner():
	n = get_world_size()
	for _ in range(n):
		CELL()
		move(North)


def with_columns(fn):
	global CELL
	CELL = fn
	n = get_world_size()
	if num_unlocked(Unlocks.Megafarm) > 0 and max_drones() > 1:
		# se il campo e' piu' grande dei droni, restringi (clear implicito)
		if max_drones() < n:
			set_world_size(max_drones())
			n = get_world_size()
		handles = []
		for i in range(n - 1):
			handles.append(spawn_drone(col_runner))
			move(East)
		col_runner()
		move(East)
		wait_drones(handles)
	else:
		for _ in range(n):
			for _ in range(n):
				fn()
				move(North)
			move(East)


def farm_hay():
	def cell():
		if can_harvest():
			harvest()
		if get_ground_type() != Grounds.Grassland:
			till()
	with_columns(cell)


def farm_wood():
	trees = num_unlocked(Unlocks.Trees) > 0
	def cell():
		et = get_entity_type()
		if can_harvest() or (et != Entities.Bush and et != Entities.Tree and et != None):
			harvest()
		if trees and (get_pos_x() + get_pos_y()) % 2 == 0:
			sow(Entities.Tree, True)
		else:
			sow(Entities.Bush, False)
	with_columns(cell)


def ensure_cost(entity, tiles):
	cost = get_cost(entity)
	if cost == None:
		return
	for item in cost:
		need = cost[item] * tiles
		if num_items(item) < need:
			farm_item(item, need)


def farm_carrots():
	n = get_world_size()
	ensure_cost(Entities.Carrot, n * n)
	def cell():
		sow(Entities.Carrot, True)
	with_columns(cell)


def farm_power():
	global PETAL_TARGET
	n = get_world_size()
	ensure_cost(Entities.Sunflower, n * n)
	clear()
	def plant_sf():
		sow(Entities.Sunflower, True)
	with_columns(plant_sf)
	t0 = get_time()
	while get_time() < t0 + 8:
		pass
	def harvest_petal():
		if measure() == PETAL_TARGET:
			fert_here()
			if can_harvest():
				harvest()
	for petals in range(15, 6, -1):
		PETAL_TARGET = petals
		with_columns(harvest_petal)


def farm_pumpkins():
	n = get_world_size()
	ensure_cost(Entities.Pumpkin, n * n)
	clear()
	for _pass in range(16):
		def plant_p():
			if get_ground_type() != Grounds.Soil:
				till()
			et = get_entity_type()
			if et == Entities.Dead_Pumpkin or et == None:
				if num_items(Items.Carrot) > 0:
					plant(Entities.Pumpkin)
			water_here()
			if et != None and et != Entities.Dead_Pumpkin:
				fert_here()
		with_columns(plant_p)
		# tutti harvestable?
		all_ok = True
		for y in range(n):
			for x in range(n):
				goto(x, y)
				if not can_harvest():
					all_ok = False
		if all_ok:
			break
	goto(0, 0)
	harvest()


def plant_cactus_cell():
	if get_ground_type() != Grounds.Soil:
		till()
	if get_entity_type() != Entities.Cactus:
		if num_items(Items.Pumpkin) < 1:
			farm_item(Items.Pumpkin, get_world_size() * get_world_size())
		plant(Entities.Cactus)


def fill_cactus():
	n = get_world_size()
	missing = True
	while missing:
		missing = False
		ensure_cost(Entities.Cactus, n * n)
		with_columns(plant_cactus_cell)
		for y in range(n):
			for x in range(n):
				goto(x, y)
				if get_entity_type() != Entities.Cactus:
					missing = True
					plant_cactus_cell()


def farm_cactus():
	n = get_world_size()
	# allinea il campo ai droni PRIMA del costo, sennò plant fallisce a meta'
	if num_unlocked(Unlocks.Megafarm) > 0 and max_drones() > 1:
		if max_drones() < n:
			set_world_size(max_drones())
			n = get_world_size()
	clear()
	fill_cactus()
	n = get_world_size()
	for y in range(n):
		for i in range(n):
			swapped = False
			for j in range(n - 1 - i):
				goto(j, y)
				a = measure()
				b = measure(East)
				if a != None and b != None and a > b:
					swap(East)
					swapped = True
			if not swapped:
				break
	for x in range(n):
		for i in range(n):
			swapped = False
			for j in range(n - 1 - i):
				goto(x, j)
				a = measure()
				b = measure(North)
				if a != None and b != None and a > b:
					swap(North)
					swapped = True
			if not swapped:
				break
	goto(0, 0)
	harvest()


def maze_search():
	facing = North
	while get_entity_type() != Entities.Treasure:
		if move(RIGHT[facing]):
			facing = RIGHT[facing]
		elif move(facing):
			pass
		elif move(LEFT[facing]):
			facing = LEFT[facing]
		else:
			facing = OPP[facing]
			move(facing)
	harvest()


def farm_gold(need):
	n = get_world_size()
	sub = n * 2 ** (num_unlocked(Unlocks.Mazes) - 1)
	# un treasure vale `sub` oro
	missing = need - num_items(Items.Gold)
	if missing < 1:
		return
	mazes_needed = missing // sub + 2
	farm_item(Items.Weird_Substance, mazes_needed * sub)
	while num_items(Items.Gold) < need:
		if num_items(Items.Weird_Substance) < sub:
			farm_item(Items.Weird_Substance, sub)
		clear()
		plant(Entities.Bush)
		use_item(Items.Weird_Substance, sub)
		maze_search()


def farm_bones(need):
	n = get_world_size()
	mult = 2 ** (num_unlocked(Unlocks.Dinosaurs) - 1)
	per = (n * n - 1) * (n * n - 1) * mult
	runs = (need - num_items(Items.Bone)) // max(1, per) + 1
	farm_item(Items.Cactus, runs * n * n + n)
	while num_items(Items.Bone) < need:
		clear()
		goto(0, 0)
		change_hat(Hats.Dinosaur_Hat)
		alive = True
		while alive:
			for x in range(n):
				if x % 2 == 0:
					steps = n - 1
					d = North
				else:
					steps = n - 1
					d = South
				for _ in range(steps):
					if not move(d):
						alive = False
						break
				if not alive:
					break
				if x < n - 1:
					if not move(East):
						alive = False
						break
			if alive:
				while get_pos_x() > 0:
					if not move(West):
						alive = False
						break
				if alive:
					while get_pos_y() > 0:
						if not move(South):
							alive = False
							break
		change_hat(Hats.Straw_Hat)


def farm_item(item, num):
	while num_items(item) < num:
		if item == Items.Hay:
			farm_hay()
		elif item == Items.Wood:
			if num_unlocked(Unlocks.Plant) > 0:
				farm_wood()
			else:
				farm_hay()
		elif item == Items.Carrot:
			farm_carrots()
		elif item == Items.Power:
			farm_power()
		elif item == Items.Pumpkin:
			farm_pumpkins()
		elif item == Items.Weird_Substance:
			before = num_items(Items.Weird_Substance)
			farm_pumpkins()
			if num_items(Items.Weird_Substance) <= before:
				sow(Entities.Tree, True)
				fert_here()
				if can_harvest():
					harvest()
		elif item == Items.Cactus:
			farm_cactus()
		elif item == Items.Bone:
			farm_bones(num)
		elif item == Items.Gold:
			farm_gold(num)
		elif item == Items.Water or item == Items.Fertilizer:
			do_a_flip()
		else:
			do_a_flip()
			return


def unlock_tech(tech):
	cost = get_cost(tech)
	if cost != None:
		for item in cost:
			farm_item(item, cost[item])
	if not unlock(tech):
		unlock_tech(tech)
	if tech == Unlocks.Expand:
		refresh_ws()
	quick_print("unlocked", tech)


def run():
	refresh_ws()
	quick_print("Fastest Reset")
	t0 = get_time()
	for tech in ORDER:
		if num_unlocked(Unlocks.Leaderboard) > 0:
			break
		unlock_tech(tech)
	while num_unlocked(Unlocks.Leaderboard) == 0:
		unlock_tech(Unlocks.Leaderboard)
	quick_print("done", get_time() - t0)
	do_a_flip()


if num_unlocked(Unlocks.Speed) == 0 and num_unlocked(Unlocks.Plant) == 0:
	run()
else:
	quick_print("Avvia via leaderboard_run/simulate, non sul save live")
