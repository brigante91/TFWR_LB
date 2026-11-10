# === IN-GAME SCRIPT ===  code window "hay_spawn_test"
# Valida il coordinamento via spawn_drone(func, T, P) (niente send/receive).
# L'harvester raccoglie erba, legge (T,P), spawna un planter che va in P, pianta T e muore.
# Conta quante delle N raccolte sono boostate.
#
# Lancia: simulate("hay_spawn_test", Unlocks, {}, {}, 746272860, 1)
# Atteso: quasi tutte boostate (81920) dopo il transiente.

HAY = Items.Hay
GRASS = Entities.Grass
BUSH = Entities.Bush
S = get_world_size()
N = 40


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


def planter(t, p):
	# drone usa-e-getta: va in p, assicura il companion t, poi muore (funzione finisce)
	goto(p[0], p[1])
	if get_entity_type() != t:
		if get_entity_type() != None:
			harvest()
		if t != BUSH:
			if get_ground_type() != Grounds.Soil:
				till()
		plant(t)


gx = get_pos_x()
gy = get_pos_y()

if get_entity_type() != GRASS:
	plant(GRASS)

# warm-up: 5 cicli per riempire il campo di companion, poi cronometro
for i in range(5):
	while not can_harvest():
		pass
	harvest()
	c, p = get_companion()
	spawn_drone(planter, c, p)

t0 = get_tick_count()
boosted = 0
for i in range(N):
	while not can_harvest():
		pass
	before = num_items(HAY)
	harvest()
	if num_items(HAY) - before == 81920:
		boosted += 1
	c, p = get_companion()
	spawn_drone(planter, c, p)
t1 = get_tick_count()
dt = t1 - t0

quick_print("boosted", boosted)
quick_print("t0", t0)
quick_print("t1", t1)
quick_print("dt", dt)
if boosted > 0:
	quick_print("tick_per_boost", dt / boosted)
