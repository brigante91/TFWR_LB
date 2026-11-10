# === IN-GAME SCRIPT ===  code window "hay_pair_test"
# Valida il loop harvester<->helper via send/receive su UNA coppia di droni.
# L'harvester (drone 0) raccoglie erba e manda (tipo,P) all'helper (drone 1),
# che va in P e pianta il companion. Conta quante delle N raccolte sono boostate.
#
# Lancia: simulate("hay_pair_test", Unlocks, {}, {}, 746272860, 1)
# Atteso: quasi tutte boostate (81920) dopo il transiente iniziale.

HAY = Items.Hay
GRASS = Entities.Grass
BUSH = Entities.Bush
S = get_world_size()
N = 40
HELPER = 1          # id del primo drone spawnato


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


def place(t, p):
	# vai in p e assicura che ci sia un'entita' di tipo t
	goto(p[0], p[1])
	if get_entity_type() != t:
		if get_entity_type() != None:
			harvest()
		if t != BUSH:                       # bush su grassland; carrot/tree su soil
			if get_ground_type() != Grounds.Soil:
				till()
		plant(t)


def helper():
	# gira finche' il programma vive: riceve richieste e pianta companion
	while True:
		m = receive()
		if m == None:
			pass
		else:
			place(m[0], m[1])


gx = get_pos_x()
gy = get_pos_y()
spawn_drone(helper)

if get_entity_type() != GRASS:
	plant(GRASS)

boosted = 0
for i in range(N):
	while not can_harvest():
		pass
	before = num_items(HAY)
	harvest()
	if num_items(HAY) - before == 81920:
		boosted += 1
	c, p = get_companion()
	send((c, p), HELPER)

quick_print("boosted", boosted, "di", N)
