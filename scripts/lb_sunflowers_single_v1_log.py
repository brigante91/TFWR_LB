# Leaderboard Sunflowers_Single: 10.000 Power, 1 drone, farm 8x8.
# Copia di lb_sunflowers_single_v1.py con le stampe per capire dove va il tempo (7 nov 2026).
# Stessa logica; le stampe costano pochi tick (quick_print e get_time costano 0).
# Righe stampate:
#   ciclo N inizio: tempo, power
#   semina: tempo, durata, quante celle per valore 7..15, azioni acqua, serbatoio, celle piantate
#   fase V: tempo, raccolti, mosse, secondi di attesa crescita, power
#   fine: tempo, cicli, raccolti totali, attesa totale, azioni acqua totali
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
	ciclo = 0
	tot_racc = 0
	tot_att = 0
	tot_acqua = 0
	while True:
		t_ciclo = get_time()
		quick_print("ciclo", ciclo, "inizio", t_ciclo, "power", num_items(POWER))
		acqua = 0
		piantate = 0
		# buckets[0..8] corrispondono ai petali da 7 a 15
		buckets = [[], [], [], [], [], [], [], [], []]

		# 1. Sweep di semina e censimento (64 mosse fisse a zero bytecode overhead)
		for step in SWEEP:
			if first_cycle:
				if get_ground_type() != SOIL:
					till()

			if get_entity_type() == None:
				plant(SUN)
				piantate += 1

			v = measure()
			if get_water() < 0.75:
				use_item(WATER)
				acqua += 1

			buckets[v - 7].append((get_pos_x(), get_pos_y()))
			move(step)

		first_cycle = False
		tot_acqua += acqua
		quick_print("  semina fine", get_time(), "durata", get_time() - t_ciclo, "valori 7..15", len(buckets[0]), len(buckets[1]), len(buckets[2]), len(buckets[3]), len(buckets[4]), len(buckets[5]), len(buckets[6]), len(buckets[7]), len(buckets[8]), "acqua", acqua, "serbatoio", num_items(WATER), "piantate", piantate)

		# 2. Raccolta decrescente (da 15 a 7)
		collected = 0
		v = 15
		while v >= 7:
			cells = buckets[v - 7]
			n = len(cells)
			r0 = collected
			att = 0
			mosse = 0
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
						mx = (pos[0] - get_pos_x()) % S
						my = (pos[1] - get_pos_y()) % S
						mosse += min(mx, S - mx) + min(my, S - my)
						goto(pos[0], pos[1])
						ta = get_time()
						while not can_harvest():
							pass
						att += get_time() - ta
						harvest()
						collected += 1
						if num_items(POWER) >= STOP:
							quick_print("fine", get_time(), "cicli", ciclo + 1, "raccolti", tot_racc + collected, "attesa", tot_att + att, "azioni acqua", tot_acqua, "power", num_items(POWER))
							clear()
							return
				else:
					idx = n - 1
					while idx >= 0:
						if collected >= MAX_HARVEST:
							break
						pos = cells[idx]
						mx = (pos[0] - get_pos_x()) % S
						my = (pos[1] - get_pos_y()) % S
						mosse += min(mx, S - mx) + min(my, S - my)
						goto(pos[0], pos[1])
						ta = get_time()
						while not can_harvest():
							pass
						att += get_time() - ta
						harvest()
						collected += 1
						if num_items(POWER) >= STOP:
							quick_print("fine", get_time(), "cicli", ciclo + 1, "raccolti", tot_racc + collected, "attesa", tot_att + att, "azioni acqua", tot_acqua, "power", num_items(POWER))
							clear()
							return
						idx -= 1

			if n > 0:
				tot_att += att
				quick_print("  fase", v, "fine", get_time(), "raccolti", collected - r0, "mosse", mosse, "attesa", att, "power", num_items(POWER))
			if collected >= MAX_HARVEST:
				break
			v -= 1
		tot_racc += collected
		ciclo += 1


run()
