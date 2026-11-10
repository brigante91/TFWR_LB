# Leaderboard Sunflowers_Single: 10.000 Power, 1 drone, farm 8x8. v5 del 7 nov 2026 (dalla v4).
# v4 in gioco: 4:56 (simulata 4:52.2). Il simulatore (haysim/sunsingle.py) conta ~222.000 tick
# di codice per run, ~36 s: quasi tutti nella ricerca della cella piu' vicina (~20-23 operazioni
# per candidata, a volte due passaggi). Modifiche:
# 1. Ricerca piu' economica: coordinate delle 64 celle precalcolate (XS, YS) e tabella della
#    distanza toroidale TD (15 voci): distanza = TD[XS[k] - ox] + TD[YS[k] - oy], ~7 operazioni.
#    Un solo passaggio trova insieme la piu' vicina gia' cresciuta (stima) e la piu' vicina in
#    assoluto: ~14 operazioni per candidata invece di ~23.
# 2. Ultimo ciclo: si seminano solo i raccolti che mancano all'obiettivo (+3 di margine), le
#    celle vuote piu' vicine, invece di tutte.
# 3. Acqua alla semina sotto 0.5 invece di 0.6.
# Misura (32 seed, differenza appaiata con la v4):
#   v4    4:52.21 simulati
#   v5    4:42.45 simulati con 13 operazioni per candidata (-9.77 +- 0.35 s), 4:44.86 con 15
#         (-7.36 +- 0.32 s). Il simulatore e' ottimista di ~1%: attesi ~4:47-4:49 in gioco.
#
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
WT = 0.5          # alla semina annaffia (fino a 1) solo se la cella ha meno di WT
RL = 14           # ripianto immediato ai livelli >= RL
G = 2             # il seme ripiantato deve valere al massimo livello - G
BOOT_D = 3        # avvio: distanza massima della cella da raccogliere durante la prima semina
END_M = 3         # ultimo ciclo: raccolti seminati in piu' di quelli che mancano

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

# distanza toroidale su 8 per una differenza d in -7..7: TD[d + 7]
TD = [1, 2, 3, 4, 3, 2, 1, 0, 1, 2, 3, 4, 3, 2, 1]
XS = []
YS = []
for _c in range(S * S):
	XS.append(_c % S)
	YS.append(_c // S)


def goto_c(c):
	# va alla cella c = y * S + x col giro toroidale piu' corto
	dx = (XS[c] - get_pos_x()) % S
	if dx <= 4:
		for _ in range(dx):
			move(East)
	else:
		for _ in range(S - dx):
			move(West)
	dy = (YS[c] - get_pos_y()) % S
	if dy <= 4:
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


def pick(L, est):
	# indice in L della cella piu' vicina fra quelle gia' cresciute (stima), altrimenti della
	# piu' vicina in assoluto; un solo passaggio
	ox = get_pos_x() - 7
	oy = get_pos_y() - 7
	now = get_time()
	br = -1
	bdr = 99
	ba = 0
	bda = 99
	j = 0
	for k in L:
		d = TD[XS[k] - ox] + TD[YS[k] - oy]
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


def nearest_any(L):
	# indice in L della cella piu' vicina (per la semina)
	ox = get_pos_x() - 7
	oy = get_pos_y() - 7
	ba = 0
	bda = 99
	j = 0
	for k in L:
		d = TD[XS[k] - ox] + TD[YS[k] - oy]
		if d < bda:
			bda = d
			ba = j
		j += 1
	return ba


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
	if len(L) == 0:
		return False
	j = pick(L, est)
	k = L[j]
	if est[k] > get_time():
		return False
	c = get_pos_y() * S + get_pos_x()
	if TD[XS[k] - XS[c] + 7] + TD[YS[k] - YS[c] + 7] > BOOT_D:
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
		# 1. Semina delle celle vuote (tutte; all'ultimo ciclo solo quelle che servono)
		need = 99
		if not first:
			need = (STOP - num_items(POWER)) / 7.8 // 1 + END_M
		if first or (S * S - nsun <= need):
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
			while len(todo) > 0 and need > 0:
				c = todo.pop(nearest_any(todo))
				goto_c(c)
				sow(c, vals, est, buckets)
				nsun += 1
				need -= 1
		first = False

		# 2. Discesa dal 15 con ripianto immediato ai livelli alti
		lvl = 15
		while nsun >= BUF and lvl >= 7:
			L = buckets[lvl]
			if len(L) == 0:
				lvl -= 1
				continue
			c = L.pop(pick(L, est))
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
