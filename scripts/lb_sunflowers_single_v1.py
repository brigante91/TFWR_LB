# Leaderboard Sunflowers_Single: 10.000 Power, 1 drone, farm 8x8.
# Copia di riferimento dello script provato dall'utente il 7 nov 2026: 5:23.470 in gioco, #7 (il #1 e' circa 3:0x).
GOAL = 10000
STOP = GOAL + 5  # margine di arresto immediato

SUN = Entities.Sunflower
SOIL = Grounds.Soil
WATER = Items.Water
POWER = Items.Power
S = 8
BUFFER = 10
MAX_HARVEST = S * S - BUFFER  # 54 raccolti utili per ciclo

# Sequenza continua di 64 mosse (serpentina 8x8 con ritorno toroidale a 0,0)
SWEEP = (
	East, East, East, East, East, East, East, North,
	West, West, West, West, West, West, West, North,
	East, East, East, East, East, East, East, North,
	West, West, West, West, West, West, West, North,
	East, East, East, East, East, East, East, North,
	West, West, West, West, West, West, West, North,
	East, East, East, East, East, East, East, North,
	West, West, West, West, West, West, West, North,
)


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


def run():
	first_cycle = True
	while True:
		# buckets[0..8] corrispondono ai petali da 7 a 15
		buckets = [[], [], [], [], [], [], [], [], []]

		# 1. Sweep di semina e censimento (64 mosse fisse a zero bytecode overhead)
		for step in SWEEP:
			if first_cycle:
				if get_ground_type() != SOIL:
					till()

			if get_entity_type() == None:
				plant(SUN)

			v = measure()
			if get_water() < 0.75:
				use_item(WATER)

			buckets[v - 7].append((get_pos_x(), get_pos_y()))
			move(step)

		first_cycle = False

		# 2. Raccolta decrescente (da 15 a 7)
		collected = 0
		v = 15
		while v >= 7:
			cells = buckets[v - 7]
			n = len(cells)
			if n > 0:
				cx = get_pos_x()
				cy = get_pos_y()

				# Ottimizzazione del percorso: percorre la lista dall'estremo più vicino
				ax, ay = cells[0]
				bx, by = cells[n - 1]
				dist_a = min((ax - cx) % S, (cx - ax) % S) + min((ay - cy) % S, (cy - ay) % S)
				dist_b = min((bx - cx) % S, (cx - bx) % S) + min((by - cy) % S, (cy - by) % S)

				if dist_a <= dist_b:
					for pos in cells:
						if collected >= MAX_HARVEST:
							break
						goto(pos[0], pos[1])
						while not can_harvest():
							pass
						harvest()
						collected += 1
						if num_items(POWER) >= STOP:
							clear()
							return
				else:
					idx = n - 1
					while idx >= 0:
						if collected >= MAX_HARVEST:
							break
						pos = cells[idx]
						goto(pos[0], pos[1])
						while not can_harvest():
							pass
						harvest()
						collected += 1
						if num_items(POWER) >= STOP:
							clear()
							return
						idx -= 1

			if collected >= MAX_HARVEST:
				break
			v -= 1


run()
