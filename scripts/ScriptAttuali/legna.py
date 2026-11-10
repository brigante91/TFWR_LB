EXTRA = 7400000000  # legno da produrre
W = 0.5             # acqua: crescita = 7s / (1 + 4*W)

S = get_world_size()
TREE = Entities.Tree
GRASS = Entities.Grass
TARGET = num_items(Items.Wood) + EXTRA


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
	# accetta solo Grass su una cella d'erba (celle con x+y dispari)
	c, pos = get_companion()
	while c != GRASS or (pos[0] + pos[1]) % 2 == 0:
		old = (c, pos)
		plant(TREE)  # se ripiantare sopra l'albero acerbo funziona: un'azione sola
		c, pos = get_companion()
		if (c, pos) == old:
			harvest()  # altrimenti: togli l'albero acerbo e ripianta
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
	goto(x, x % 2)  # prima cella con x+y pari
	for i in range(S // 2):
		plant(TREE)
		water_up()
		reroll()
		move(North)
		move(North)
	while num_items(Items.Wood) < TARGET:
		for i in range(S // 2):
			tree_cell()
			move(North)
			move(North)
		if x == 0:
			quick_print("legno", num_items(Items.Wood))


def make_column(x):
	def fn():
		column(x)
	return fn


clear()
quick_print("fattoria", S, "drone", max_drones(), "legno ora", num_items(Items.Wood))
for x in range(1, S):
	spawn_drone(make_column(x))
column(0)