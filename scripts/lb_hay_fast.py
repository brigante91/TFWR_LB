# === IN-GAME ===  code window "lb_hay_fast"   (metodo plant-companion parallelo, v1)
# Harvester (colonne multiple di 4) raccolgono erba e batchano i companion;
# planter usa-e-getta spawnati con un batch piantano i companion esatti e muoiono.
# Niente re-roll: ogni raccolta tende al boost ×160. Niente send/receive (non disponibili).
#
# Lancia come leaderboard (riporta il tempo):
#   leaderboard_run(Leaderboards.Hay, "lb_hay_fast", 1000000)
# oppure prova/cronometra con simulate.

GOAL = 2000000000
HAY = Items.Hay
GRASS = Entities.Grass
BUSH = Entities.Bush
S = get_world_size()

NHARV = 8               # harvester persistenti
STEP = S // NHARV       # distanza tra colonne harvester (= 4 su 32)
BATCH = 6               # companion per planter (ammortizza lo spawn=200)
W = 0.6                 # acqua per crescita piu' veloce


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


def planter(batch):
	# pianta ogni (tipo, pos) del batch, poi muore
	for tp in batch:
		t = tp[0]
		p = tp[1]
		if p[0] % STEP == 0:
			continue            # non toccare le colonne degli harvester
		goto(p[0], p[1])
		if get_entity_type() != t:
			if get_entity_type() != None:
				harvest()
			if t != BUSH:
				if get_ground_type() != Grounds.Soil:
					till()
			plant(t)


def harvester(col):
	goto(col, 0)
	batch = []
	while num_items(HAY) < GOAL:
		e = get_entity_type()
		if e == None:
			plant(GRASS)
		elif e == GRASS:
			if can_harvest():
				if get_water() < W and num_items(Items.Water) > 16:
					use_item(Items.Water)
				harvest()
				c, p = get_companion()
				batch = batch + [(c, p)]
				if len(batch) >= BATCH:
					spawn_drone(planter, batch)
					batch = []
		move(North)


def make_h(col):
	def fn():
		harvester(col)
	return fn


clear()
for k in range(1, NHARV):
	spawn_drone(make_h(k * STEP))
harvester(0)
