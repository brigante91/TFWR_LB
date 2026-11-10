# === IN-GAME SCRIPT ===  code window "hay_boost_test"
# Valida il mattone del metodo veloce: piantando il companion RICHIESTO dall'erba,
# il raccolto e' boostato (atteso 81920) invece che no (atteso 512).
#
# Lancia (seed esplicito, ripetibile):
#   simulate("hay_boost_test", Unlocks, {}, {}, 746272860, 1)
# Incolla l'output: righe A_no_companion / companion / planted / B_with_companion.

HAY = Items.Hay
GRASS = Entities.Grass
BUSH = Entities.Bush
S = get_world_size()


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


gx = get_pos_x()
gy = get_pos_y()

# assicura erba matura sotto il drone
if get_entity_type() != GRASS:
	if get_ground_type() != Grounds.Soil:
		plant(GRASS)
while not can_harvest():
	pass

# --- CASO A: raccolgo SENZA piazzare il companion (atteso NON boostato) ---
before = num_items(HAY)
harvest()
quick_print("A_no_companion", num_items(HAY) - before)

# l'erba e' ricresciuta con un nuovo companion (T, P)
c, p = get_companion()
quick_print("companion", c, p)

# --- CASO B: piazzo il companion richiesto in P, torno, raccolgo (atteso BOOSTATO) ---
goto(p[0], p[1])
if get_entity_type() != c:
	if get_entity_type() != None:
		harvest()
	if c != BUSH:            # bush cresce su grassland; carrot/tree su soil
		if get_ground_type() != Grounds.Soil:
			till()
	planted = plant(c)
else:
	planted = True
quick_print("planted", planted, "ora", get_entity_type())

goto(gx, gy)
while not can_harvest():
	pass
before = num_items(HAY)
harvest()
quick_print("B_with_companion", num_items(HAY) - before)
