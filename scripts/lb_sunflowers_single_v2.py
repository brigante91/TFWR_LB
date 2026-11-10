# Leaderboard Sunflowers_Single: 10.000 Power, 1 drone, farm 8x8. v2 del 7 nov 2026 (dalla v1).
# Simulatore: haysim/sunsingle.py (stesse regole tarate di sunsim2.py: crescita 7 s, serbatoio
# 25.6/s, flag del bonus, consumo di power, meta' velocita' a power 0). Taratura: la v1 fa
# 5:27.1 simulati contro 5:23.470 in gioco, senza ritocchi.
# Modifiche rispetto alla v1:
# 1. Acqua: si annaffia solo alla semina e solo se la cella ha meno di 0.6, riempiendola fino a 1
#    con UNA azione da piu' unita' (la v1 dava 1 unita' a quasi ogni cella a ogni ciclo:
#    ~35 azioni da 200 tick per ciclo contro ~11). L'acqua resta nella cella dopo il raccolto e
#    un drone solo ha il serbatoio quasi tutto per se'.
# 2. Raccolta: dentro ogni valore si va sempre alla cella piu' vicina (distanza toroidale)
#    invece di seguire la lista dall'estremo piu' vicino: ~2.4 mosse per raccolto invece di ~3.
# 3. 55 raccolti per ciclo invece di 54: il 55esimo vede ancora 10 girasoli in campo, lui
#    compreso (Sunflower.Harvest conta il campo prima di togliere la pianta).
# 4. Liste per valore indicizzate direttamente col valore e niente tuple: meno operazioni.
# Misura (40 seed, stesse sequenze casuali, errore standard):
#   v1    5:26.05 +- 0.50
#   v2    5:04.93 +- 0.39   (differenza appaiata -21.12 +- 0.52 s; il giro al piu' vicino
#         costa ~17 operazioni per candidata, contate)
# Provate e scartate: ripianto immediato durante la discesa (il seme nuovo va aspettato:
# +100..+390 s), accettare solo valori alti in semina (MINV 9: +4 s, MINV 11: +47 s), soglie
# d'acqua 0.3-0.5 e 0.75 (peggio di 0.6). Le mosse costano 200 tick e restano ~3.6 per
# raccolto (semina compresa): e' il limite di questo schema; il #1 (~3:0x) deve raccogliere
# con ~1 mossa per raccolto.
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
	while True:
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
				vals[c] = measure()
				w = get_water()
				if w < WT:
					x = (1 - w) * 4
					n = x // 1
					if n < x:
						n += 1
					use_item(WATER, n)
			buckets[vals[c]].append(c)
			move(step)
		first = False

		# 2. Discesa dal 15: sempre la cella piu' vicina fra quelle del valore corrente
		got = 0
		lvl = 15
		while got < HMAX and lvl >= 7:
			L = buckets[lvl]
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
				goto_c(c)
				while not can_harvest():
					pass
				harvest()
				vals[c] = 0
				got += 1
				if num_items(POWER) >= STOP:
					clear()
					return
			lvl -= 1


run()
