EXTRA = 42000000   # zucche da produrre in questa esecuzione
WATER_TO = 0.5     # livello d'acqua alla semina (crescita 0,5/(1+4*acqua))

S = get_world_size()
PUMPKIN = Entities.Pumpkin
DEAD = Entities.Dead_Pumpkin
TARGET = num_items(Items.Pumpkin) + EXTRA


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


def seed_cell():
	if get_ground_type() != Grounds.Soil:
		till()
	plant(PUMPKIN)
	while get_water() < WATER_TO and num_items(Items.Water) > 16:
		use_item(Items.Water)


def column(x):
	# primo passaggio: semina tutta la colonna
	goto(x, 0)
	for y in range(S):
		t = get_entity_type()
		if t == DEAD:
			harvest()
			t = None
		if t != PUMPKIN:
			seed_cell()
		move(North)

	# poi ripassa solo le caselle non ancora mature
	pending = []
	for y in range(S):
		pending.append(y)
	while len(pending) > 0:
		left = []
		for y in pending:
			goto(x, y)
			t = get_entity_type()
			if t == DEAD:
				harvest()
				seed_cell()
				left.append(y)
			elif t != PUMPKIN:
				seed_cell()
				left.append(y)
			elif not can_harvest():
				left.append(y)
		pending = left


def make_column(x):
	def fn():
		column(x)
	return fn


clear()
quick_print("fattoria", S, "drone", max_drones(), "zucche ora", num_items(Items.Pumpkin))

while num_items(Items.Pumpkin) < TARGET:
	handles = []
	for x in range(1, S):
		h = spawn_drone(make_column(x))
		if h != None:
			handles.append(h)
	column(0)
	for h in handles:
		wait_for(h)

	before = num_items(Items.Pumpkin)
	goto(0, 0)
	harvest()
	quick_print("zucca gigante:", num_items(Items.Pumpkin) - before, "totale", num_items(Items.Pumpkin))