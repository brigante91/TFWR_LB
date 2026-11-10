# Leaderboard Sunflowers_Single: 10.000 Power, 1 drone, farm 8x8. v9 del 7 nov 2026.
# Unione della v8 dell'utente (4:28.13 in gioco) e della v7 (4:34.059):
#  dalla v8: ripianto immediato ai livelli >= 13 (finche' il massimo rimasto e' >= 13) con
#    rilancio solo se il seme vale almeno il massimo rimasto (il seme scartato e' sempre un
#    massimo: il flag non si sporca mai); il seme che vale massimo - 1 viene annaffiato fino a
#    0.85; ricerca con un solo confronto per candidata e uscita a distanza <= 1; ricerca senza
#    stima di crescita ai livelli bassi; caso con una sola cella senza ricerca.
#  dalla v7: percorsi precalcolati PATHS (239 tuple, verificate su tutte le coppie), controllo
#    dell'obiettivo a contatore, rilancio dei 15 piantati dopo il passo 46 della serpentina,
#    semina leggera dopo il primo ciclo.
# Simulatore (haysim/sunsingle.py, 24 seed, rispetto alla v6): regola di ripianto della v8
# -6.18 +- 0.65 s; con i 15 tardivi -7.98 +- 0.61 s. RL 12 uguale, RL 11 +5 s, RL 10 +18 s.
# In gioco v6 4:39.7 -> v8 4:28.13 (-11.6 s, compresi i tagli di codice della v8): con i 15
# tardivi e i percorsi precalcolati attesi ~4:24-4:26.
#
GOAL = 10000
STOP = GOAL + 5   # margine: con 1 drone UsePower toglie ~0.2 power ogni 0.2 s
S = 8
BUF = 10          # girasoli da lasciare in campo (bonus solo con >= 10, quello raccolto compreso)
WT = 0.5          # alla semina annaffia (fino a 1) solo se la cella ha meno di WT
RL = 13           # ripianto immediato ai livelli >= RL (finche' il massimo rimasto e' >= RL)
BOOT_D = 3        # avvio: distanza massima della cella da raccogliere durante la prima semina
END_M = 3         # ultimo ciclo: raccolti seminati in piu' di quelli che mancano
LATE = 46         # dopo questo passo della serpentina i 15 si rilanciano (non crescerebbero in tempo)

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

# Celle come codice k = y * 16 + x. Per cc = codice del drone - 119:
#   T[k - cc]     = distanza toroidale su 8x8
#   PATHS[k - cc] = mosse dal drone alla cella k (prima est/ovest, poi nord/sud)
T = [
	2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3, 2, 0, 3, 4, 5, 6, 5, 4, 3, 2, 3, 4, 5, 6, 5, 4,
	3, 0, 4, 5, 6, 7, 6, 5, 4, 3, 4, 5, 6, 7, 6, 5, 4, 0, 5, 6, 7, 8, 7, 6, 5, 4, 5, 6, 7, 8,
	7, 6, 5, 0, 4, 5, 6, 7, 6, 5, 4, 3, 4, 5, 6, 7, 6, 5, 4, 0, 3, 4, 5, 6, 5, 4, 3, 2, 3, 4,
	5, 6, 5, 4, 3, 0, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3, 2, 0, 1, 2, 3, 4, 3, 2, 1, 0,
	1, 2, 3, 4, 3, 2, 1, 0, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3, 2, 0, 3, 4, 5, 6, 5, 4,
	3, 2, 3, 4, 5, 6, 5, 4, 3, 0, 4, 5, 6, 7, 6, 5, 4, 3, 4, 5, 6, 7, 6, 5, 4, 0, 5, 6, 7, 8,
	7, 6, 5, 4, 5, 6, 7, 8, 7, 6, 5, 0, 4, 5, 6, 7, 6, 5, 4, 3, 4, 5, 6, 7, 6, 5, 4, 0, 3, 4,
	5, 6, 5, 4, 3, 2, 3, 4, 5, 6, 5, 4, 3, 0, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3, 2,
]
PATHS = [
	(East, North), (East, East, North), (East, East, East, North),
	(East, East, East, East, North), (West, West, West, North), (West, West, North),
	(West, North), (North,), (East, North), (East, East, North), (East, East, East, North),
	(East, East, East, East, North), (West, West, West, North), (West, West, North),
	(West, North), (), (East, North, North), (East, East, North, North),
	(East, East, East, North, North), (East, East, East, East, North, North),
	(West, West, West, North, North), (West, West, North, North), (West, North, North),
	(North, North), (East, North, North), (East, East, North, North),
	(East, East, East, North, North), (East, East, East, East, North, North),
	(West, West, West, North, North), (West, West, North, North), (West, North, North), (),
	(East, North, North, North), (East, East, North, North, North),
	(East, East, East, North, North, North), (East, East, East, East, North, North, North),
	(West, West, West, North, North, North), (West, West, North, North, North),
	(West, North, North, North), (North, North, North), (East, North, North, North),
	(East, East, North, North, North), (East, East, East, North, North, North),
	(East, East, East, East, North, North, North), (West, West, West, North, North, North),
	(West, West, North, North, North), (West, North, North, North), (),
	(East, North, North, North, North), (East, East, North, North, North, North),
	(East, East, East, North, North, North, North),
	(East, East, East, East, North, North, North, North),
	(West, West, West, North, North, North, North), (West, West, North, North, North, North),
	(West, North, North, North, North), (North, North, North, North),
	(East, North, North, North, North), (East, East, North, North, North, North),
	(East, East, East, North, North, North, North),
	(East, East, East, East, North, North, North, North),
	(West, West, West, North, North, North, North), (West, West, North, North, North, North),
	(West, North, North, North, North), (), (East, South, South, South),
	(East, East, South, South, South), (East, East, East, South, South, South),
	(East, East, East, East, South, South, South), (West, West, West, South, South, South),
	(West, West, South, South, South), (West, South, South, South), (South, South, South),
	(East, South, South, South), (East, East, South, South, South),
	(East, East, East, South, South, South), (East, East, East, East, South, South, South),
	(West, West, West, South, South, South), (West, West, South, South, South),
	(West, South, South, South), (), (East, South, South), (East, East, South, South),
	(East, East, East, South, South), (East, East, East, East, South, South),
	(West, West, West, South, South), (West, West, South, South), (West, South, South),
	(South, South), (East, South, South), (East, East, South, South),
	(East, East, East, South, South), (East, East, East, East, South, South),
	(West, West, West, South, South), (West, West, South, South), (West, South, South), (),
	(East, South), (East, East, South), (East, East, East, South),
	(East, East, East, East, South), (West, West, West, South), (West, West, South),
	(West, South), (South,), (East, South), (East, East, South), (East, East, East, South),
	(East, East, East, East, South), (West, West, West, South), (West, West, South),
	(West, South), (), (East,), (East, East), (East, East, East), (East, East, East, East),
	(West, West, West), (West, West), (West,), (), (East,), (East, East), (East, East, East),
	(East, East, East, East), (West, West, West), (West, West), (West,), (), (East, North),
	(East, East, North), (East, East, East, North), (East, East, East, East, North),
	(West, West, West, North), (West, West, North), (West, North), (North,), (East, North),
	(East, East, North), (East, East, East, North), (East, East, East, East, North),
	(West, West, West, North), (West, West, North), (West, North), (), (East, North, North),
	(East, East, North, North), (East, East, East, North, North),
	(East, East, East, East, North, North), (West, West, West, North, North),
	(West, West, North, North), (West, North, North), (North, North), (East, North, North),
	(East, East, North, North), (East, East, East, North, North),
	(East, East, East, East, North, North), (West, West, West, North, North),
	(West, West, North, North), (West, North, North), (), (East, North, North, North),
	(East, East, North, North, North), (East, East, East, North, North, North),
	(East, East, East, East, North, North, North), (West, West, West, North, North, North),
	(West, West, North, North, North), (West, North, North, North), (North, North, North),
	(East, North, North, North), (East, East, North, North, North),
	(East, East, East, North, North, North), (East, East, East, East, North, North, North),
	(West, West, West, North, North, North), (West, West, North, North, North),
	(West, North, North, North), (), (East, North, North, North, North),
	(East, East, North, North, North, North), (East, East, East, North, North, North, North),
	(East, East, East, East, North, North, North, North),
	(West, West, West, North, North, North, North), (West, West, North, North, North, North),
	(West, North, North, North, North), (North, North, North, North),
	(East, North, North, North, North), (East, East, North, North, North, North),
	(East, East, East, North, North, North, North),
	(East, East, East, East, North, North, North, North),
	(West, West, West, North, North, North, North), (West, West, North, North, North, North),
	(West, North, North, North, North), (), (East, South, South, South),
	(East, East, South, South, South), (East, East, East, South, South, South),
	(East, East, East, East, South, South, South), (West, West, West, South, South, South),
	(West, West, South, South, South), (West, South, South, South), (South, South, South),
	(East, South, South, South), (East, East, South, South, South),
	(East, East, East, South, South, South), (East, East, East, East, South, South, South),
	(West, West, West, South, South, South), (West, West, South, South, South),
	(West, South, South, South), (), (East, South, South), (East, East, South, South),
	(East, East, East, South, South), (East, East, East, East, South, South),
	(West, West, West, South, South), (West, West, South, South), (West, South, South),
	(South, South), (East, South, South), (East, East, South, South),
	(East, East, East, South, South), (East, East, East, East, South, South),
	(West, West, West, South, South), (West, West, South, South), (West, South, South), (),
	(East, South), (East, East, South), (East, East, East, South),
	(East, East, East, East, South), (West, West, West, South), (West, West, South),
	(West, South), (South,), (East, South), (East, East, South), (East, East, East, South),
	(East, East, East, East, South), (West, West, West, South), (West, West, South),
	(West, South),
]

def here():
	return get_pos_y() * 16 + get_pos_x()


def fill(wt):
	# annaffia la cella sotto il drone fino a 1 se ha meno di wt (una sola azione); True se annaffiata
	w = get_water()
	if w < wt:
		x = (1 - w) * 4
		n = x // 1
		if n < x:
			n += 1
		use_item(WATER, n)
		return True
	return False


def grow_est(watered):
	# stima prudente dell'ora di crescita della cella appena piantata
	if watered:
		return get_time() + 1.7
	return get_time() + 8.4 / (1 + 4 * get_water())


def pick(L, est):
	# indice in L della cella piu' vicina gia' cresciuta (stima), altrimenti della piu' vicina
	cc = here() - 119
	now = get_time()
	br = -1
	bdr = 99
	ba = 0
	bda = 99
	j = 0
	for k in L:
		d = T[k - cc]
		if d < bda:
			bda = d
			ba = j
		if d < bdr:
			if est[k] <= now:
				bdr = d
				br = j
		j += 1
	if br >= 0:
		return br
	return ba


def boot(buckets, est, vals):
	# avvio: raccoglie un massimo gia' cresciuto (stima) vicino e torna; True se ha raccolto
	mx = 15
	while mx > 7 and len(buckets[mx]) == 0:
		mx -= 1
	L = buckets[mx]
	if len(L) == 0:
		return False
	j = pick(L, est)
	k = L[j]
	if est[k] > get_time():
		return False
	c = here()
	if T[k - c + 119] > BOOT_D:
		return False
	L.pop(j)
	for d in PATHS[k - c + 119]:
		move(d)
	while not can_harvest():
		pass
	harvest()
	vals[k] = 0
	for d in PATHS[c - k + 119]:
		move(d)
	return True


def run():
	vals = []
	est = []
	for _ in range(128):
		vals.append(0)
		est.append(0)
	buckets = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
	nsun = 0

	# 1a. Prima semina: till, semina e avvio a velocita' piena
	piantate = 0
	i = 0
	for step in SWEEP:
		i += 1
		if piantate >= 10:
			if num_items(POWER) == 0:
				if boot(buckets, est, vals):
					nsun -= 1
		c = here()
		if get_ground_type() != SOIL:
			till()
		if vals[c] == 0:
			plant(SUN)
			v = measure()
			if i > LATE:
				while v == 15:
					harvest()
					plant(SUN)
					v = measure()
			vals[c] = v
			buckets[v].append(c)
			est[c] = grow_est(fill(WT))
			nsun += 1
			piantate += 1
		move(step)
	first = True

	while True:
		if not first:
			# 1b. Semina delle celle vuote (all'ultimo ciclo solo quelle che servono)
			need = (STOP - num_items(POWER)) / 7.8 // 1 + END_M
			if S * S - nsun <= need:
				i = 0
				for step in SWEEP:
					i += 1
					c = here()
					if vals[c] == 0:
						plant(SUN)
						v = measure()
						if i > LATE:
							while v == 15:
								harvest()
								plant(SUN)
								v = measure()
						vals[c] = v
						buckets[v].append(c)
						est[c] = grow_est(fill(WT))
						nsun += 1
					move(step)
			else:
				todo = []
				for y in range(S):
					for x in range(S):
						if vals[y * 16 + x] == 0:
							todo.append(y * 16 + x)
				while len(todo) > 0 and need > 0:
					cc = here() - 119
					ba = 0
					bda = 99
					j = 0
					for k in todo:
						d = T[k - cc]
						if d < bda:
							bda = d
							ba = j
						j += 1
					c = todo.pop(ba)
					for d in PATHS[c - cc]:
						move(d)
					plant(SUN)
					v = measure()
					vals[c] = v
					buckets[v].append(c)
					est[c] = grow_est(fill(WT))
					nsun += 1
					need -= 1
		first = False
		# raccolti prima dei quali l'obiettivo non puo' essere raggiunto (ognuno rende <= 8)
		left = (STOP - num_items(POWER)) / 8 // 1

		# 2. Discesa dal 15 con ripianto immediato ai livelli alti
		lvl = 15
		while lvl >= 7 and nsun >= BUF:
			L = buckets[lvl]
			while len(L) > 0 and nsun >= BUF:
				cc = here() - 119
				if len(L) == 1:
					c = L.pop()
				elif lvl >= RL - 1:
					# piu' vicina gia' cresciuta (stima), altrimenti piu' vicina; esce a d <= 1
					now = get_time()
					br = -1
					bdr = 99
					ba = 0
					bda = 99
					j = 0
					for k in L:
						d = T[k - cc]
						if d < bdr:
							if est[k] <= now:
								if d <= 1:
									br = j
									break
								bdr = d
								br = j
							elif d < bda:
								bda = d
								ba = j
						j += 1
					if br >= 0:
						ba = br
					c = L.pop(ba)
				else:
					# livelli bassi: gia' cresciute, solo la piu' vicina; esce a d <= 1
					ba = 0
					bda = 99
					j = 0
					for k in L:
						d = T[k - cc]
						if d < bda:
							if d <= 1:
								ba = j
								break
							bda = d
							ba = j
						j += 1
					c = L.pop(ba)
				for d in PATHS[c - cc]:
					move(d)
				if not can_harvest():
					fill(0.99)
					while not can_harvest():
						pass
				harvest()
				vals[c] = 0
				nsun -= 1
				left -= 1
				if left <= 0:
					if num_items(POWER) >= STOP:
						clear()
						return
				if lvl >= RL:
					# massimo rimasto nel campo (tutte le liste sopra lvl sono vuote)
					mx = lvl
					while len(buckets[mx]) == 0:
						mx -= 1
					if mx >= RL:
						plant(SUN)
						u = measure()
						# rilancia solo se u >= mx: il seme scartato e' un massimo, flag pulito
						while u >= mx:
							harvest()
							plant(SUN)
							u = measure()
						vals[c] = u
						buckets[u].append(c)
						nsun += 1
						if u == mx - 1:
							est[c] = grow_est(fill(0.85))
						else:
							est[c] = grow_est(fill(WT))
			lvl -= 1

run()
