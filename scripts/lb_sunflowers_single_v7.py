# Leaderboard Sunflowers_Single: 10.000 Power, 1 drone, farm 8x8. v7 del 7 nov 2026 (dalla v6).
# v6 in gioco: 4:39.7. Stessa logica della v6 (stesse celle, stesso ordine, stessi reroll), meno
# operazioni dell'interprete:
# 1. Spostamenti con percorsi precalcolati: PATHS[k - cc] e' la tupla di mosse dalla cella del
#    drone alla cella k (stesso giro toroidale piu' corto di prima), una tabella letterale di
#    239 voci verificata su tutte le 4096 coppie. ~5 operazioni invece di ~15 per spostamento.
# 2. La ricerca della cella piu' vicina e' scritta dentro la discesa: la posizione del drone si
#    legge una volta per raccolto e serve sia alla ricerca sia al percorso.
# 3. L'obiettivo si controlla solo quando i raccolti fatti potrebbero averlo raggiunto (ogni
#    raccolto rende al massimo 8): un contatore invece di num_items a ogni raccolto.
# 4. Semina: un ciclo completo solo per il primo giro (till, avvio); poi un ciclo leggero senza
#    controlli inutili. La stima di crescita usa l'acqua appena data invece di rileggerla.
# 5. Idea presa da uno script dell'utente (4:37 in gioco): nell'ultimo tratto della serpentina
#    (dopo il passo 46) un 15 appena piantato si rilancia subito. 15 e' sempre il massimo, quindi
#    raccogliere il seme non sporca il flag, e la discesa non deve aspettare la sua crescita.
#    Simulatore: -2.51 +- 0.36 s (24 seed). Scartata invece l'acqua sotto 0.7 (+2.7 s).
# Stima: ~5-7 s dal codice (profilo del simulatore) + ~2.5 s dai 15 tardivi: attesi ~4:30-4:32.
# Il limite di questo schema resta ~4:19 (codice a costo zero nel simulatore).
#
# v5 in gioco: 4:46.553. Profilo del codice nel simulatore (haysim/sunsingle.py): il 63% delle
# operazioni dell'interprete e' nella ricerca della cella piu' vicina (~16 operazioni per cella
# candidata nella v5). Unica modifica: le celle si indicano col codice k = y * 16 + x invece di
# y * 8 + x. In base 16 la differenza di due codici individua da sola lo spostamento (dx, dy),
# quindi la distanza toroidale e' una sola lettura di tabella: T[k - cc], con cc = codice del
# drone - 119. La ricerca costa ~10 operazioni per candidata. vals ed est sono lunghe 128.
# Misura (24 seed, differenza appaiata con la v5 contata a 14 operazioni per candidata):
#   v5 a 16 op/candidata (probabile costo reale)   +2.44 +- 0.19 s
#   v6 a 10 op/candidata                            -4.84 +- 0.19 s
#   quindi ~-7 s sulla v5 reale: attesi ~4:39 in gioco.
# Il limite di questo schema: con codice a costo zero il simulatore da' 4:15.9 (~4:19 in gioco).
#
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
				# cella piu' vicina gia' cresciuta (stima), altrimenti la piu' vicina
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
					ba = br
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
						est[c] = grow_est(fill(WT))
			lvl -= 1


run()
