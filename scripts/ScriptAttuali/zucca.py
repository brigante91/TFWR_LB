# Classifica Pumpkins: 2e8 zucche, 32 droni. v4 del 6 nov 2026: QUADRATI INDIPENDENTI.
# Simulatore haysim/pumpsim.py (fusione reale dei gruppi): v2 455 s, v3 415 s, v4 393 s (-5% su v3,
# -14% su v2); il simulatore e' ottimista del ~7% rispetto al gioco (v2: 486 s in gioco).
#
# Idea: la resa e' L^2 * min(L, 6) * 512 = 3072 zucche per cella per OGNI quadrato di lato >= 6,
# quindi il 32x32 non da' nessun bonus: 16 quadrati 7x7 raccolti ognuno appena completo, senza
# aspettare il resto del campo (il ciclo e' la media dei quadrati invece del massimo su 32 droni).
#
# PERCHE' I CORRIDOI (misurato con la fusione reale di PumpkinController.MergeWithOthers):
# quadrati 8x8 ADIACENTI non funzionano. Una zucca che matura entra nel quadrato piu' grande di
# zucche mature che la contiene e che non si sovrappone a gruppi esistenti: con quadrati adiacenti
# si formano continuamente gruppi "a cavallo" del confine (2x2, 3x3...) e da quel momento il
# quadrato 8x8 non puo' piu' formarsi (sovrapposizione); i gruppi a cavallo non vengono mai
# assorbiti, il campo si frammenta in gruppi di lato 1-4 e si blocca. Simulato: 8x8 adiacenti
# (test m0 sull'angolo (3,7) o (7,7), rete di sicurezza T_MAX 4/6/10 s, test "lato >= 6" con due
# celle a distanza 5) -> dopo i primi 2-3 raccolti del 32x32 solo raccolti minuscoli: 15-95 M
# zucche in 1500 s, mai finito. Con una colonna e una riga vuote tra i quadrati (non piantate,
# ci cresce l'erba: il dp conta solo zucche) nessun gruppo puo' uscire dal quadrato e il test
# e' esatto. 16 x 49 = 784 celle (76% del campo), raccolto 150528 a quadrato, 1329 raccolti.
#
# Droni: 2 per quadrato. Harvester: colonne 0-2 (21 celle, serpentina per righe da (0,0) a (2,6)).
# Partner: colonne 3-6 (28 celle, ciclo hamiltoniano, riparte da dove si trova). Per entrambi la
# logica di v3: pending list, acqua fresche 0.25 -> 0.5, ripiantate -> 1.0, attesa sul posto con
# <= 2 pendenti, fertilizzante dalla 4a morte della cella nel ciclo.
# Barriera del quadrato: tutte le zucche di un gruppo hanno il measure() della cella in basso a
# sinistra del quadrato. L'harvester legge m0 = measure() su (0,0) appena piantata (e ogni volta che
# la ripianta), poi, finito il suo blocco, si mette su (0,6) e aspetta measure() == m0: vero solo se
# (0,0) e (0,6) stanno nello stesso quadrato, cioe' lato 7 = tutto il quadrato (i corridoi
# impediscono quadrati piu' grandi). Rete di sicurezza: dopo T_MAX senza completamento raccoglie
# comunque il gruppo in cui sta (sim: ~0.2 volte per partita); il partner, se aspetta piu' di
# T_MAX_P con la cella matura sotto di se', raccoglie il suo gruppo (mai successo nel sim).
# Corsa: durante le passate una cella None vuol dire che il quadrato e' stato raccolto -> si riparte.
# Il main e' l'harvester del quadrato 0: stampa ogni suo raccolto e chiude con clear() all'obiettivo.
GOAL = 200000000

S = get_world_size()
PUMPKIN = Entities.Pumpkin
DEAD = Entities.Dead_Pumpkin
SOIL = Grounds.Soil
WATER = Items.Water
FERT = Items.Fertilizer

WLOW = 0.25     # fresche: annaffia se la cella e' sotto WLOW ...
WTGT = 0.5      # ... fino a WTGT
WREP = 1.0      # ripiantate: fino a 1.0 (con quello che c'e' nel serbatoio)
WAIT_K = 2      # con <= WAIT_K pendenti si aspetta sul posto
FERT_GEN = 4    # fertilizzante dalla FERT_GEN-esima morte della cella nel ciclo
T_MAX = 15      # s: rete di sicurezza dell'harvester
T_MAX_P = 30    # s: rete di sicurezza del partner
CHK = 18        # indice di (0, 6) nel percorso dell'harvester


def make_dirs(cells, cyclic):
	dirs = []
	n = len(cells)
	for k in range(n):
		if k == n - 1 and not cyclic:
			dirs.append(North)
		else:
			a = cells[k]
			c = cells[(k + 1) % n]
			if c[0] > a[0]:
				dirs.append(East)
			elif c[0] < a[0]:
				dirs.append(West)
			elif c[1] > a[1]:
				dirs.append(North)
			else:
				dirs.append(South)
	return dirs


def harv_cells(q):
	# colonne 0-2 del quadrato q: serpentina per righe, da (0,0) a (2,6)
	x0 = (q % 4) * 8
	y0 = (q // 4) * 8
	cells = []
	for j in range(7):
		if j % 2 == 0:
			for i in range(3):
				cells.append((x0 + i, y0 + j))
		else:
			for i in range(3):
				cells.append((x0 + 2 - i, y0 + j))
	return cells


def part_cells(q):
	# colonne 3-6 del quadrato q: ciclo hamiltoniano (riga 0 verso Est, poi le colonne da 6 a 3
	# sulle righe 1-6 alternando il verso; l'ultima cella (3,1) e' adiacente alla prima (3,0))
	x0 = (q % 4) * 8 + 3
	y0 = (q // 4) * 8
	cells = []
	for i in range(4):
		cells.append((x0 + i, y0))
	for ii in range(4):
		i = 3 - ii
		if ii % 2 == 0:
			for j in range(6):
				cells.append((x0 + i, y0 + 1 + j))
		else:
			for j in range(6):
				cells.append((x0 + i, y0 + 6 - j))
	return cells


def goto_start(cells):
	# dallo spawner (0, 0) alla prima cella, con wrap
	tx = cells[0][0]
	ty = cells[0][1]
	if tx <= S // 2:
		for _ in range(tx):
			move(East)
	else:
		for _ in range(S - tx):
			move(West)
	if ty <= S // 2:
		for _ in range(ty):
			move(North)
	else:
		for _ in range(S - ty):
			move(South)


def goto(cells, pos, k):
	# dentro il quadrato (niente wrap): da cells[pos] a cells[k]
	a = cells[pos]
	c = cells[k]
	dx = c[0] - a[0]
	dy = c[1] - a[1]
	while dx > 0:
		move(East)
		dx -= 1
	while dx < 0:
		move(West)
		dx += 1
	while dy > 0:
		move(North)
		dy -= 1
	while dy < 0:
		move(South)
		dy += 1


def water_to(target):
	# porta l'acqua della cella a target (0.25 per unita') in UNA azione; se il serbatoio non
	# basta usa quello che c'e'
	need = (target - get_water()) * 4
	n = need // 1
	if n < need:
		n += 1
	if n <= 0:
		return
	tank = num_items(WATER)
	if tank < n:
		n = tank
	if n > 0:
		use_item(WATER, n)


def run_cycle(cells, dirs, gens, pos, first, cyclic, m0ref):
	# Riempie il blocco (ciclico: da cells[pos] lungo il ciclo tornando su cells[pos]; percorso:
	# da cells[0] a cells[n-1]), poi passa sulle celle pendenti finche' sono tutte mature o il
	# quadrato e' stato raccolto (cella None). m0ref[0] = measure() di (0,0) appena piantata.
	# Ritorna l'indice della cella su cui si trova il drone.
	n = len(cells)
	pending = []
	for i in range(n):
		if cyclic:
			k = (pos + i) % n
		else:
			k = i
		if first and get_ground_type() != SOIL:
			till()
		t = get_entity_type()
		if t == DEAD:
			harvest()
			t = None
		if t == None:
			gens[k] = 0
			plant(PUMPKIN)
			if k == 0 and m0ref != None:
				m0ref[0] = measure()
			if get_water() < WLOW:
				water_to(WTGT)
			pending.append(k)
		elif not can_harvest():
			pending.append(k)
		if cyclic or k < n - 1:
			move(dirs[k])
	if not cyclic:
		pos = n - 1
	while len(pending) > 0:
		left = []
		for k in pending:
			goto(cells, pos, k)
			pos = k
			while True:
				t = get_entity_type()
				if t == PUMPKIN:
					if can_harvest():
						break
					# in crescita
					if gens[k] >= FERT_GEN and num_items(FERT) >= 1:
						use_item(FERT)
						continue
					if len(pending) > WAIT_K:
						left.append(k)
						break
				elif t == None:
					# il quadrato e' stato raccolto: il ciclo e' finito
					return pos
				else:
					# morta: ripianta subito (percorso critico)
					gens[k] += 1
					harvest()
					plant(PUMPKIN)
					if k == 0 and m0ref != None:
						m0ref[0] = measure()
					if gens[k] >= FERT_GEN and num_items(FERT) >= 1:
						use_item(FERT)
						continue
					water_to(WREP)
					if len(pending) > WAIT_K:
						left.append(k)
						break
		pending = left
	return pos


def harvester(q, is_main):
	def fn():
		cells = harv_cells(q)
		dirs = make_dirs(cells, False)
		goto_start(cells)
		gens = []
		for _ in range(len(cells)):
			gens.append(0)
		m0ref = [None]
		pos = 0
		first = True
		c = 0
		while True:
			if pos != 0:
				goto(cells, pos, 0)
				pos = 0
			pos = run_cycle(cells, dirs, gens, pos, first, False, m0ref)
			first = False
			if get_entity_type() == None:
				# raccolto da altri durante le passate: si riparte subito
				continue
			goto(cells, pos, CHK)
			pos = CHK
			t0 = get_time()
			while measure() != m0ref[0]:
				if get_time() - t0 > T_MAX:
					break
			if can_harvest():
				before = num_items(Items.Pumpkin)
				harvest()
				if is_main:
					c += 1
					quick_print("raccolto", c, "a", get_time(), "zucche", num_items(Items.Pumpkin) - before, "acqua", num_items(WATER))
					if num_items(Items.Pumpkin) >= GOAL:
						clear()
						return
	return fn


def partner(q):
	def fn():
		cells = part_cells(q)
		dirs = make_dirs(cells, True)
		goto_start(cells)
		gens = []
		for _ in range(len(cells)):
			gens.append(0)
		pos = 0
		first = True
		while True:
			pos = run_cycle(cells, dirs, gens, pos, first, True, None)
			first = False
			t0 = get_time()
			while get_entity_type() != None:
				if get_time() - t0 > T_MAX_P and can_harvest():
					harvest()
					break
	return fn


def drone_task(s):
	# drone s: quadrato s // 2, harvester se s pari, partner se s impari
	if s % 2 == 0:
		return harvester(s // 2, False)
	return partner(s // 2)


def spawn_range(lo, hi):
	while hi - lo > 1:
		mid = (lo + hi) // 2
		spawn_drone(spawn_range_task(mid, hi))
		hi = mid
	drone_task(lo)()


def spawn_range_task(lo, hi):
	def fn():
		spawn_range(lo, hi)
	return fn


clear()
spawn_drone(spawn_range_task(1, 32))
harvester(0, True)()
