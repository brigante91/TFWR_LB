# Leaderboard Sunflowers_Single: 10.000 Power, 1 drone, farm 8x8. v4 del 7 nov 2026 (dalla v3).
# v3 in gioco: 5:02.276 (simulata 4:59.30). Unica modifica: AVVIO A VELOCITA' PIENA.
# Si parte con power 0, quindi a meta' velocita', e la prima semina (64 celle con till, semina e
# acqua) dura ~17 s. Con un drone solo il consumo e' ~1 power al secondo: un solo raccolto col
# bonus (+8) da' ~8 s a velocita' piena. Durante la prima semina, dopo le prime 10 piante e
# finche' il power e' 0, se una cella col valore massimo del campo dovrebbe essere gia' cresciuta
# (stima ora di semina + 8.4 s / (1 + 4 * acqua)) ed e' a non piu' di BOOT_D passi, il drone va a
# raccoglierla e torna alla serpentina. Il flag e' pulito (nessun raccolto prima) e in campo ci
# sono gia' >= 10 girasoli, quindi il raccolto rende 8.
# Misura (haysim/sunsingle.py, prog_v4 con BOOT, 32 seed, differenza appaiata con la v3):
#   v3    4:59.30 simulati
#   v4    4:52.21 simulati (-7.08 +- 0.30 s); raggio 3 o 5 uguale. Il simulatore e' ottimista
#         di ~1% (v3: 4:59.3 simulati contro 5:02.276 in gioco): attesi ~4:55 in gioco.
#
# Modifiche rispetto alla v2:
# 1. Ripianto immediato ai livelli 15 e 14: dopo il raccolto si ripianta subito sulla stessa
#    cella e si rilancia il seme finche' vale piu' del massimo rimasto (il seme e' il massimo:
#    raccoglierlo non sporca il flag) o finche' e' a meno di G=2 livelli dal corrente (non
#    crescerebbe in tempo). Il seme tenuto entra nella sua lista e viene raccolto nello stesso
#    ciclo. Si risparmiano le visite della semina per quelle celle.
# 2. Semina solo delle celle vuote: serpentina se sono piu' di 30, altrimenti giro al piu' vicino.
#    Si risemina quando nel campo restano 10 girasoli.
# 3. Nella discesa si sceglie la cella piu' vicina fra quelle che dovrebbero gia' essere
#    cresciute (stima: ora di semina + 8.4 s / (1 + 4 * acqua), il caso peggiore); se nessuna,
#    la piu' vicina in assoluto.
# 4. Se la cella non e' ancora cresciuta, prima di aspettare la si annaffia fino a 1.
# Misura (32 seed, stesse sequenze casuali, differenza appaiata con la v2):
#   v2    5:04.97 simulati
#   v3    4:59.30 simulati (-5.68 +- 0.54 s; attesa di crescita da ~12 a ~4 s per run)
# Provate e scartate: scarto G=1 (il seme va aspettato) e G>=3 (troppi reroll), ripianto anche
# ai livelli <= 12, acqua sotto 0.7 invece di 0.6.
GOAL = 10000
STOP = GOAL + 5   # margine: con 1 drone UsePower toglie ~0.2 power ogni 0.2 s
S = 8
BUF = 10          # girasoli da lasciare in campo (bonus solo con >= 10, quello raccolto compreso)
WT = 0.6          # alla semina annaffia (fino a 1) solo se la cella ha meno di WT
RL = 14           # ripianto immediato ai livelli >= RL
G = 2             # il seme ripiantato deve valere al massimo livello - G
SNAKE_MIN = 30    # oltre questo numero di celle vuote la semina usa la serpentina
BOOT_D = 3        # avvio: distanza massima della cella da raccogliere durante la prima semina

SUN = Entities.Sunflower
SOIL = Grounds.Soil
WATER = Items.Water
POWER = Items.Power

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


def fill(wt):
	# annaffia la cella sotto il drone fino a 1 se ha meno di wt (una sola azione)
	w = get_water()
	if w < wt:
		x = (1 - w) * 4
		n = x // 1
		if n < x:
			n += 1
		use_item(WATER, n)


def nearest(L, est, only_ready):
	# indice in L della cella piu' vicina (toroidale); only_ready: solo se gia' cresciuta (stima)
	cx = get_pos_x()
	cy = get_pos_y()
	now = get_time()
	best = -1
	bd = 99
	n = len(L)
	j = 0
	while j < n:
		k = L[j]
		if not only_ready or est[k] <= now:
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
	return best


def sow(c, vals, est, buckets):
	# pianta la cella vuota sotto il drone e la registra
	plant(SUN)
	v = measure()
	vals[c] = v
	buckets[v].append(c)
	fill(WT)
	est[c] = get_time() + 8.4 / (1 + 4 * get_water())


def boot(buckets, est, vals):
	# avvio: raccoglie un massimo gia' cresciuto (stima) vicino e torna; True se ha raccolto
	mx = 15
	while mx > 7 and len(buckets[mx]) == 0:
		mx -= 1
	L = buckets[mx]
	j = nearest(L, est, True)
	if j < 0:
		return False
	k = L[j]
	c = get_pos_y() * S + get_pos_x()
	dx = abs(k % S - c % S)
	if dx > 4:
		dx = S - dx
	dy = abs(k // S - c // S)
	if dy > 4:
		dy = S - dy
	if dx + dy > BOOT_D:
		return False
	L.pop(j)
	goto_c(k)
	while not can_harvest():
		pass
	harvest()
	vals[k] = 0
	goto_c(c)
	return True


def run():
	vals = []
	est = []
	for _ in range(S * S):
		vals.append(0)
		est.append(0)
	buckets = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
	nsun = 0
	first = True
	while True:
		# 1. Semina delle celle vuote
		if first or S * S - nsun > SNAKE_MIN:
			piantate = 0
			for step in SWEEP:
				c = get_pos_y() * S + get_pos_x()
				if first and piantate >= 10 and num_items(POWER) == 0:
					if boot(buckets, est, vals):
						nsun -= 1
				if first:
					if get_ground_type() != SOIL:
						till()
				if vals[c] == 0:
					sow(c, vals, est, buckets)
					nsun += 1
					piantate += 1
				move(step)
		else:
			todo = []
			for c in range(S * S):
				if vals[c] == 0:
					todo.append(c)
			while len(todo) > 0:
				c = todo.pop(nearest(todo, est, False))
				goto_c(c)
				sow(c, vals, est, buckets)
				nsun += 1
		first = False

		# 2. Discesa dal 15 con ripianto immediato ai livelli alti
		lvl = 15
		while nsun >= BUF and lvl >= 7:
			L = buckets[lvl]
			if len(L) == 0:
				lvl -= 1
				continue
			j = nearest(L, est, True)
			if j < 0:
				j = nearest(L, est, False)
			c = L.pop(j)
			goto_c(c)
			if not can_harvest():
				fill(0.99)
				while not can_harvest():
					pass
			harvest()
			vals[c] = 0
			nsun -= 1
			if num_items(POWER) >= STOP:
				clear()
				return
			if lvl >= RL:
				# massimo rimasto nel campo (tutte le liste sopra lvl sono vuote)
				mx = lvl
				while mx >= 7 and len(buckets[mx]) == 0:
					mx -= 1
				if mx >= 7:
					plant(SUN)
					u = measure()
					while u > mx or u > lvl - G:
						harvest()
						plant(SUN)
						u = measure()
					vals[c] = u
					buckets[u].append(c)
					nsun += 1
					fill(WT)
					est[c] = get_time() + 8.4 / (1 + 4 * get_water())


run()
