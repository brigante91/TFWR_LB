# Classifica Wood: 10.000.000.000 legno, 32 drone.
# Alberi a scacchiera (x+y pari), companion Grass sulle celle d'erba.
GOAL = 10000000000
W = 0.5

S = get_world_size()
TREE = Entities.Tree
GRASS = Entities.Grass


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


def reroll():
	c, pos = get_companion()
	while c != GRASS or (pos[0] + pos[1]) % 2 == 0:
		old = (c, pos)
		plant(TREE)
		c, pos = get_companion()
		if (c, pos) == old:
			harvest()
			plant(TREE)
			c, pos = get_companion()


def water_up():
	while get_water() < W and num_items(Items.Water) > 16:
		use_item(Items.Water)


def tree_cell():
	while not can_harvest():
		pass
	harvest()
	plant(TREE)
	reroll()


def column(x):
	goto(x, x % 2)
	for i in range(S // 2):
		plant(TREE)
		water_up()
		reroll()
		move(North)
		move(North)
	while num_items(Items.Wood) < GOAL:
		for i in range(S // 2):
			tree_cell()
			move(North)
			move(North)
			if num_items(Items.Wood) >= GOAL:
				return


def make_column(x):
	def fn():
		column(x)
	return fn


clear()
for x in range(1, S):
	spawn_drone(make_column(x))
column(0)
