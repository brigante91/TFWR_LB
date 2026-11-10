# Copia di lb_sunflowers_single_v2.py con le stampe per capire dove va il tempo (7 nov 2026).
# Stessa logica; quick_print e get_time costano 0 tick, i contatori pochi tick.
# Righe stampate:
#   ciclo N inizio: tempo, power
#   semina: tempo, durata, celle per valore 7..15, piantate, azioni acqua, serbatoio
#   fase V: tempo, raccolti, mosse, secondi di attesa crescita, power
#   fine: tempo, cicli, raccolti totali, attesa totale, azioni acqua totali, power
GOAL = 10000
STOP = GOAL + 5   # margine: con 1 drone UsePower toglie ~0.2 power ogni 0.2 s
S = 8
HMAX = 55         # raccolti per ciclo
WT = 0.6          # annaffia (fino a 1) solo se la cella ha meno di WT

SUN = Entities.Sunflower
SOIL = Grounds.Soil
WATER = Items.Water
POWER = Items.Power

# Serpentina continua di 64 mosse (8x8 con ritorno toroidale al punto di partenza)
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


def goto_c(c):
	# va alla cella c = y * S + x col giro toroidale piu' corto
	dx = (c % S - get_pos_x()) % S
	if dx <= S // 2:
		for _ in range(dx):
			move(East)
	else:
		for _ in range(S - dx):
			move(West)
	dy = (c // S - get_pos_y()) % S
	if dy <= S // 2:
		for _ in range(dy):
			move(North)
	else:
		for _ in range(S - dy):
			move(South)


def run():
	vals = []
	for _ in range(S * S):
		vals.append(0)
	first = True
	ciclo = 0
	tot_racc = 0
	tot_att = 0
	tot_acqua = 0
	while True:
		t_ciclo = get_time()
		quick_print("ciclo", ciclo, "inizio", t_ciclo, "power", num_items(POWER))
		acqua = 0
		piantate = 0
		# buckets[v] = celle col valore v (indice = petali, 7..15)
		buckets = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]

		# 1. Serpentina: pianta le celle vuote, annaffia solo se serve, censisce tutte le celle
		for step in SWEEP:
			c = get_pos_y() * S + get_pos_x()
			if first:
				if get_ground_type() != SOIL:
					till()
			if vals[c] == 0:
				plant(SUN)
				piantate += 1
				vals[c] = measure()
				w = get_water()
				if w < WT:
					x = (1 - w) * 4
					n = x // 1
					if n < x:
						n += 1
					use_item(WATER, n)
					acqua += 1
			buckets[vals[c]].append(c)
			move(step)
		first = False
		tot_acqua += acqua
		quick_print("  semina fine", get_time(), "durata", get_time() - t_ciclo, "valori 7..15", len(buckets[7]), len(buckets[8]), len(buckets[9]), len(buckets[10]), len(buckets[11]), len(buckets[12]), len(buckets[13]), len(buckets[14]), len(buckets[15]), "piantate", piantate, "acqua", acqua, "serbatoio", num_items(WATER))

		# 2. Discesa dal 15: sempre la cella piu' vicina fra quelle del valore corrente
		got = 0
		lvl = 15
		while got < HMAX and lvl >= 7:
			L = buckets[lvl]
			r0 = got
			att = 0
			mosse = 0
			while len(L) > 0 and got < HMAX:
				cx = get_pos_x()
				cy = get_pos_y()
				best = 0
				bd = 99
				n = len(L)
				j = 0
				while j < n:
					k = L[j]
					dx = abs(k % S - cx)
					if dx > 4:
						dx = S - dx
					dy = abs(k // S - cy)
					if dy > 4:
						dy = S - dy
					if dx + dy < bd:
						bd = dx + dy
						best = j
					j += 1
				c = L.pop(best)
				mosse += bd
				goto_c(c)
				ta = get_time()
				while not can_harvest():
					pass
				att += get_time() - ta
				harvest()
				vals[c] = 0
				got += 1
				if num_items(POWER) >= STOP:
					tot_racc += got
					tot_att += att
					quick_print("  fase", lvl, "fine", get_time(), "raccolti", got - r0, "mosse", mosse, "attesa", att, "power", num_items(POWER))
					quick_print("fine", get_time(), "cicli", ciclo + 1, "raccolti", tot_racc, "attesa", tot_att, "azioni acqua", tot_acqua, "power", num_items(POWER))
					clear()
					return
			if got > r0:
				quick_print("  fase", lvl, "fine", get_time(), "raccolti", got - r0, "mosse", mosse, "attesa", att, "power", num_items(POWER))
			tot_att += att
			lvl -= 1
		tot_racc += got
		ciclo += 1


run()
