# Classifica Sunflowers: 100.000 power, 32 drone. NON ANCORA PROVATO.
# Il bonus arriva raccogliendo un girasole con il massimo dei petali del campo.
# I petali vanno da 7 a 15: ogni drone ripianta finche' esce 15, cosi' ogni
# girasole maturo e' un massimo e da' il bonus.
GOAL = 100000
MAXP = 15

S = get_world_size()
SUN = Entities.Sunflower


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


def plant_max():
	plant(SUN)
	tries = 0
	while measure() != MAXP and tries < 60:
		harvest()  # toglie il girasole acerbo
		plant(SUN)
		tries += 1


def column(x):
	goto(x, 0)
	while num_items(Items.Power) < GOAL:
		for y in range(S):
			if get_ground_type() != Grounds.Soil:
				till()
			t = get_entity_type()
			if t != SUN:
				if t != None:
					harvest()
				plant_max()
			elif can_harvest():
				harvest()
				plant_max()
			move(North)
			if num_items(Items.Power) >= GOAL:
				return


def make_column(x):
	def fn():
		column(x)
	return fn


clear()
for x in range(1, S):
	spawn_drone(make_column(x))
column(0)
